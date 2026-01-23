import { getRankingDistribution, getMasterEvolutionData } from '@/lib/data-service'
import { RankingsChart } from './rankings-view'
import { MasterTable } from './master-table'

// Server Component Wrapper
export async function RankingsContainer({ importId, domain }: { importId: string, domain: string }) {
    const distribution = await getRankingDistribution(importId, domain)
    const masterData = await getMasterEvolutionData(importId, domain)

    return (
        <div className="space-y-8">
            <div className="grid gap-4 md:grid-cols-2">
                <RankingsChart data={distribution} />
                {/* Placeholder for future summary widgets */}
            </div>

            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold tracking-tight">Keyword Evolution</h3>
                    {/* Add filters here if needed */}
                </div>
                <MasterTable data={masterData} />
            </div>
        </div>
    )
}
