import { getRankingDistribution } from '@/lib/data-service'
import { RankingsChart } from './rankings-view'

// Server Component Wrapper
export async function RankingsContainer({ importId, domain }: { importId: string, domain: string }) {
    const distribution = await getRankingDistribution(importId, domain)

    return (
        <div className="grid gap-4 md:grid-cols-2">
            <RankingsChart data={distribution} />
            {/* Future: Add "Movements" table here */}
        </div>
    )
}
