import Papa from 'papaparse'

export interface NormalizedRow {
    keyword: string
    group: string | null
    difficulty: number | null
    searches: number | null
    impressions: number | null
    ctr: number | null
    competition: string | null
    cpcAvg: number | null
    cpcMin: number | null
    cpcMax: number | null
    trend3m: string | null
    rankings: Record<string, DomainRankingData>
}

export interface DomainRankingData {
    visibility: number | null
    position: number | null
    outOfTop20: boolean
    url: string | null
}

export interface ParseResult {
    rows: NormalizedRow[]
    domains: string[]
    error?: string
}

// Helpers
const cleanStr = (s: any) => typeof s === 'string' ? s.trim() : ''
const isND = (s: any) => {
    if (!s) return true
    const str = String(s).trim().toUpperCase()
    return str === 'N/D' || str === '' || str === '-'
}

const parsePct = (val: any): number | null => {
    if (isND(val)) return null
    const str = String(val).replace('%', '').replace(',', '.').trim()
    const num = parseFloat(str)
    return isNaN(num) ? null : num
}

const parseCurrency = (val: any): number | null => {
    if (isND(val)) return null
    const str = String(val).replace('$', '').replace('€', '').replace(',', '.').trim()
    const num = parseFloat(str)
    return isNaN(num) ? null : num
}

const parseIntSafe = (val: any): number | null => {
    if (isND(val)) return null
    const str = String(val).replace(/\./g, '').replace(',', '').trim() // Remove thousands separators
    const num = parseInt(str, 10)
    return isNaN(num) ? null : num
}

const parsePos = (val: any): { pos: number | null; out: boolean } => {
    if (isND(val)) return { pos: null, out: false }
    const str = String(val).trim()
    if (str.toLowerCase().includes('no está') || str.toLowerCase().includes('not in')) {
        return { pos: 21, out: true } // Bucket > 20
    }
    const num = parseInt(str, 10)
    if (isNaN(num)) return { pos: null, out: false }
    // Check if val > 20
    if (num > 20) return { pos: num, out: true }
    return { pos: num, out: false }
}

export const parseCSV = async (fileContent: string): Promise<ParseResult> => {
    return new Promise((resolve) => {
        Papa.parse(fileContent, {
            header: true,
            skipEmptyLines: true,
            complete: (results) => {
                if (results.errors.length && results.data.length === 0) {
                    resolve({ rows: [], domains: [], error: 'Error parsing CSV' })
                    return
                }

                const rawRows = results.data as Record<string, any>[]
                if (!rawRows.length) {
                    resolve({ rows: [], domains: [], error: 'CSV is empty' })
                    return
                }

                // Detect Domains from Headers
                // Look for keys like "Visibilidad [domain.com]"
                const headers = Object.keys(rawRows[0])
                const domainSet = new Set<string>()

                headers.forEach(h => {
                    if (h.startsWith('Visibilidad ')) {
                        const domain = h.replace('Visibilidad ', '').trim()
                        if (domain) domainSet.add(domain)
                    }
                })

                const domains = Array.from(domainSet)
                const rows: NormalizedRow[] = []

                rawRows.forEach(row => {
                    // Base Metrics
                    const normalized: NormalizedRow = {
                        keyword: cleanStr(row['Palabra clave']),
                        group: cleanStr(row['Grupo Palabra Clave']) || 'Sin grupo',
                        difficulty: parseIntSafe(row['Google Dificultad Palabra Clave']),
                        searches: parseIntSafe(row['# de búsquedas']),
                        impressions: parseIntSafe(row['Impresiones']),
                        ctr: parsePct(row['CTR']),
                        competition: isND(row['Competencia']) ? null : cleanStr(row['Competencia']),
                        cpcAvg: parseCurrency(row['CPC prom.']),
                        cpcMin: parseCurrency(row['CPC mín.']),
                        cpcMax: parseCurrency(row['CPC máx.']),
                        trend3m: isND(row['Cambio de 3 meses (Tendencia)']) ? null : String(row['Cambio de 3 meses (Tendencia)']),
                        rankings: {}
                    }

                    // Domain Metrics
                    domains.forEach(domain => {
                        const visKey = `Visibilidad ${domain}`
                        const posKey = `Posición en Google ${domain}`
                        const urlKey = `Google URL encontrada ${domain}`

                        const posData = parsePos(row[posKey])

                        normalized.rankings[domain] = {
                            visibility: parsePct(row[visKey]),
                            position: posData.pos,
                            outOfTop20: posData.out,
                            url: isND(row[urlKey]) ? null : cleanStr(row[urlKey])
                        }
                    })

                    rows.push(normalized)
                })

                resolve({ rows, domains })
            },
            error: (err: any) => {
                resolve({ rows: [], domains: [], error: err.message })
            }
        })
    })
}
