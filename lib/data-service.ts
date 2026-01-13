import { prisma } from '@/lib/db'

export interface ExecutiveSummaryData {
    totalVisibility: number
    sov: number
    top3: number
    top10: number
    top20: number
    outOf20: number
    avgPosition: number
    strikingDistance: number // Pos 4-10
    totalKeywords: number
}

/**
 * Calculates KPIs for the Executive Summary for a specific Import and Domain.
 * Only considers rankings stored in DomainRanking table.
 */
export async function getExecutiveSummary(importId: string, domain: string): Promise<ExecutiveSummaryData> {
    // 1. Get all rankings for this domain in this import to calc stats
    const myRankings = await prisma.domainRanking.findMany({
        where: {
            importId,
            domain
        },
        select: {
            visibility: true,
            position: true,
            outOfTop20: true
        }
    })

    // 2. Calculate "My" stats
    let totalVisibility = 0
    let top3 = 0
    let top10 = 0
    let top20 = 0
    let outOf20 = 0
    let sumPos = 0
    let countPos = 0
    let strikingDistance = 0

    for (const r of myRankings) {
        if (r.visibility) totalVisibility += r.visibility

        if (r.outOfTop20 || (r.position && r.position > 20)) {
            outOf20++
        } else if (r.position) {
            if (r.position <= 3) top3++
            if (r.position <= 10) top10++
            if (r.position <= 20) top20++

            if (r.position >= 4 && r.position <= 10) strikingDistance++

            sumPos += r.position
            countPos++
        }
    }

    const avgPosition = countPos > 0 ? sumPos / countPos : 0

    // 3. Calculate SoV (My Visibility / Sum of All Domains Visibility in this import)
    // We need the sum of visibility for ALL rankings in this import
    const allRankings = await prisma.domainRanking.aggregate({
        where: { importId },
        _sum: { visibility: true }
    })

    const totalMarketVisibility = allRankings._sum.visibility || 0
    const sov = totalMarketVisibility > 0 ? (totalVisibility / totalMarketVisibility) * 100 : 0

    return {
        totalVisibility,
        sov,
        top3,
        top10,
        top20, // Note: top10 is subset of top20 usually, but requirements imply buckets. 
        // If buckets are exclusive: 1-3, 4-10, 11-20. 
        // But typical SEO Requirement "Keywords in Top 10" implies cumulative.
        // While "Distribution" charts usually want exclusive buckets.
        // I will return cumulative here as requested "Keywords in Top 3 / Top 10 / Top 20"
        // For charts, we can subtract.
        outOf20,
        avgPosition,
        strikingDistance,
        totalKeywords: myRankings.length
    }
}

export async function getDomainsInImport(importId: string) {
    const domains = await prisma.domainRanking.findMany({
        where: { importId },
        distinct: ['domain'],
        select: { domain: true }
    })
    return domains.map(d => d.domain)
}

export interface CompetitorMetric {
    domain: string
    visibility: number
    sov: number
    top10: number
    avgPos: number
}

export async function getCompetitorAnalysis(importId: string): Promise<CompetitorMetric[]> {
    // Get all domains rankings with aggregation
    // Prisma groupBy or manual aggregation. Manual is safer for complex logic.
    const allRankings = await prisma.domainRanking.findMany({
        where: { importId },
        select: { domain: true, visibility: true, position: true }
    })

    // Calculate total market visibility for SoV
    const totalMarketVis = allRankings.reduce((sum, r) => sum + (r.visibility || 0), 0)

    // Group by domain
    const domainStats = new Map<string, { vis: number, top10: number, sumPos: number, count: number }>()

    for (const r of allRankings) {
        if (!domainStats.has(r.domain)) {
            domainStats.set(r.domain, { vis: 0, top10: 0, sumPos: 0, count: 0 })
        }
        const stats = domainStats.get(r.domain)!

        if (r.visibility) stats.vis += r.visibility

        if (r.position && r.position <= 20) { // Limit avg pos to ranked ones or handle out of 20? 
            // Usually avg pos is calculated on ranked keywords.
            stats.sumPos += r.position
            stats.count++
            if (r.position <= 10) stats.top10++
        }
    }

    const result: CompetitorMetric[] = []
    for (const [domain, stats] of domainStats.entries()) {
        result.push({
            domain,
            visibility: stats.vis,
            sov: totalMarketVis > 0 ? (stats.vis / totalMarketVis) * 100 : 0,
            top10: stats.top10,
            avgPos: stats.count > 0 ? stats.sumPos / stats.count : 0
        })
    }

    return result.sort((a, b) => b.visibility - a.visibility)
}

export interface RankingBucket {
    range: string
    count: number
    color: string
}

export async function getRankingDistribution(importId: string, domain: string): Promise<RankingBucket[]> {
    const rankings = await prisma.domainRanking.findMany({
        where: { importId, domain },
        select: { position: true, outOfTop20: true }
    })

    let top3 = 0
    let pos4_10 = 0
    let pos11_20 = 0
    let pos20plus = 0

    for (const r of rankings) {
        if (r.outOfTop20 || (r.position && r.position > 20)) {
            pos20plus++
        } else if (r.position) {
            if (r.position <= 3) top3++
            else if (r.position <= 10) pos4_10++
            else if (r.position <= 20) pos11_20++
            else pos20plus++
        } else {
            pos20plus++ // Null position
        }
    }

    return [
        { range: 'Top 3', count: top3, color: '#16a34a' }, // Green
        { range: '4-10', count: pos4_10, color: '#84cc16' }, // Light Green
        { range: '11-20', count: pos11_20, color: '#eab308' }, // Yellow
        { range: '20+', count: pos20plus, color: '#ef4444' } // Red
    ]
}

export interface Opportunity {
    keyword: string
    position: number
    volume: number
    difficulty: number
    url: string
    type: 'Quick Win' | 'Striking Distance'
}

export async function getOpportunities(importId: string, domain: string): Promise<Opportunity[]> {
    const rankings = await prisma.domainRanking.findMany({
        where: {
            importId,
            domain,
            position: { gte: 4, lte: 20 }
        },
        include: {
            keyword: {
                include: { metrics: { where: { importId } } }
            }
        }
    })

    // Transform and Sort
    const opportunities: Opportunity[] = rankings.map(r => {
        const metric = r.keyword.metrics[0]
        const volume = metric?.volume || 0
        const difficulty = metric?.difficulty || 0

        return {
            keyword: r.keyword.text,
            position: r.position!,
            volume,
            difficulty,
            url: r.url || '',
            type: r.position! <= 10 ? 'Quick Win' : 'Striking Distance'
        }
    })

    // Sort by Volume DESC, then Position ASC
    return opportunities.sort((a, b) => {
        if (b.volume !== a.volume) return b.volume - a.volume
        return a.position - b.position
    })
}

export interface GroupMetric {
    name: string
    count: number
    totalVis: number
    avgPos: number
    top10: number
}

export async function getGroupAnalysis(importId: string): Promise<GroupMetric[]> {
    const groups = await prisma.keyword.groupBy({
        by: ['group'],
        where: { metrics: { some: { importId } } },
        _count: { text: true },
    })

    // We need detailed metrics to calc visibility/pos per group
    // Ideally this is a raw query or more complex aggregation.
    // For MVP, we iterate over groups and fetch aggregate.

    const results: GroupMetric[] = []

    for (const g of groups) {
        if (!g.group) continue;

        // Aggregations for this group
        const metrics = await prisma.keywordMetric.findMany({
            where: {
                importId,
                keyword: { group: g.group }
            },
            include: { keyword: { include: { rankings: { where: { importId, domain: 'radiofonics.com' } } } } } // Assuming radiofonics for now
            // Limitation: Ideally calculate for "Current Domain" passed in args
        })
        // FIX: getGroupAnalysis should take 'domain' arg. Assuming hardcoded for now or fixing in next refactor? 
        // Let's stick to "radiofonics.com" pattern or rely on default until I update signature.
        // Actually, I can pass domain if I update signature.
        // Let's keep it simple: we aggregate rankings.
    }
    return [] // Stub to be replaced by correct implementation below with domain arg
}

export async function getGroupAnalysisWithDomain(importId: string, domain: string): Promise<GroupMetric[]> {
    const keywords = await prisma.keyword.findMany({
        where: { metrics: { some: { importId } } },
        select: {
            group: true,
            rankings: {
                where: { importId, domain },
                select: { visibility: true, position: true }
            }
        }
    })

    const groupMap = new Map<string, { count: number, vis: number, sumPos: number, posCount: number, top10: number }>()

    for (const k of keywords) {
        const gName = k.group || 'No Group'
        if (!groupMap.has(gName)) groupMap.set(gName, { count: 0, vis: 0, sumPos: 0, posCount: 0, top10: 0 })

        const stats = groupMap.get(gName)!
        stats.count++

        const r = k.rankings[0]
        if (r) {
            if (r.visibility) stats.vis += r.visibility
            if (r.position) {
                stats.sumPos += r.position
                stats.posCount++
                if (r.position <= 10) stats.top10++
            }
        }
    }

    const result: GroupMetric[] = []
    for (const [name, stats] of groupMap.entries()) {
        result.push({
            name,
            count: stats.count,
            totalVis: stats.vis,
            avgPos: stats.posCount > 0 ? stats.sumPos / stats.posCount : 0,
            top10: stats.top10
        })
    }

    return result.sort((a, b) => b.totalVis - a.totalVis)
}


export interface UrlMetric {
    url: string
    count: number
    vis: number
    top10: number
}

export async function getUrlAnalysis(importId: string, domain: string): Promise<UrlMetric[]> {
    const rankings = await prisma.domainRanking.groupBy({
        by: ['url'],
        where: { importId, domain },
        _count: { keywordId: true },
        _sum: { visibility: true },
    })

    const results: UrlMetric[] = []

    // Need to get Top 10 count per URL. groupBy doesn't support "conditional count" easily.
    // We can fetch url + position and aggregate manually or use raw query.
    // Manual approach for flexibility:

    const allRankings = await prisma.domainRanking.findMany({
        where: { importId, domain },
        select: { url: true, visibility: true, position: true }
    })

    const urlMap = new Map<string, { count: number, vis: number, top10: number }>()

    for (const r of allRankings) {
        if (!r.url) continue;
        if (!urlMap.has(r.url)) urlMap.set(r.url, { count: 0, vis: 0, top10: 0 })

        const stats = urlMap.get(r.url)!
        stats.count++
        if (r.visibility) stats.vis += r.visibility
        if (r.position && r.position <= 10) stats.top10++
    }

    for (const [url, stats] of urlMap.entries()) {
        results.push({ url, count: stats.count, vis: stats.vis, top10: stats.top10 })
    }

    return results.sort((a, b) => b.vis - a.vis)
}
