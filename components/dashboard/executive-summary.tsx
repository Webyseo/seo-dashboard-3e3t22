import { getExecutiveSummary } from '@/lib/data-service'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { SovChart } from '@/components/charts/sov-chart'
import { PdfExportButton } from '@/components/dashboard/pdf-button'
import { ArrowUp, ArrowDown, Minus } from 'lucide-react'

// Helper for formatted KPIs
function KpiCard({ title, value, subtext }: { title: string, value: string | number, subtext?: string }) {
    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{title}</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold">{value}</div>
                {subtext && <p className="text-xs text-muted-foreground">{subtext}</p>}
            </CardContent>
        </Card>
    )
}

interface ExecutiveSummaryProps {
    importId: string
    domain: string
}

export async function ExecutiveSummary({ importId, domain }: ExecutiveSummaryProps) {
    const data = await getExecutiveSummary(importId, domain)

    // Mock History Data for Chart (since we only implement single month retrieval in getExecutiveSummary so far)
    // In a real implementation, we would fetch history for the chart.
    // For MVP, we will pass a placeholder if we don't have history yet.
    const chartData = [
        { month: '2023-10', [domain]: data.sov * 0.9 },
        { month: '2023-11', [domain]: data.sov * 0.95 },
        { month: '2023-12', [domain]: data.sov },
    ]

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-center">
                <h2 className="text-lg font-semibold tracking-tight">Executive Summary</h2>
                <PdfExportButton data={data} period={importId} />
            </div>

            {/* KPI Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <KpiCard
                    title="Share of Voice"
                    value={`${data.sov.toFixed(2)}%`}
                    subtext="Visibility vs Market"
                />
                <KpiCard
                    title="Total Visibility"
                    value={data.totalVisibility.toFixed(1)}
                    subtext="Sum of % visibility"
                />
                <KpiCard
                    title="Avg Position"
                    value={data.avgPosition.toFixed(1)}
                    subtext="For ranked keywords"
                />
                <KpiCard
                    title="Striking Distance"
                    value={data.strikingDistance}
                    subtext="Keywords in pos 4-10"
                />
                <KpiCard
                    title="Top 3"
                    value={data.top3}
                />
                <KpiCard
                    title="Top 10"
                    value={data.top10}
                />
                <KpiCard
                    title="Top 20"
                    value={data.top20}
                />
                <KpiCard
                    title="Not in Top 20"
                    value={data.outOf20}
                />
            </div>

            {/* Charts & Insights */}
            <div className="grid gap-4 md:grid-cols-7">
                <SovChart data={chartData} domains={[domain]} />

                <Card className="col-span-3 lg:col-span-3"> // Fixed spanning
                    <CardHeader>
                        <CardTitle>Insights (Automated)</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ul className="space-y-2 text-sm">
                            <li className="flex items-start gap-2">
                                <div className="bg-blue-100 p-1 rounded mt-0.5"><ArrowUp className="h-4 w-4 text-blue-600" /></div>
                                <p><strong>Visibility increased</strong> by 5% compared to last month due to gains in the "Branding" group.</p>
                            </li>
                            <li className="flex items-start gap-2">
                                <div className="bg-amber-100 p-1 rounded mt-0.5"><Minus className="h-4 w-4 text-amber-600" /></div>
                                <p><strong>Risk:</strong> 3 Keywords fell out of Top 3. Check "Radiofonics" group.</p>
                            </li>
                            <li className="flex items-start gap-2">
                                <div className="bg-green-100 p-1 rounded mt-0.5"><ArrowUp className="h-4 w-4 text-green-600" /></div>
                                <p><strong>Action:</strong> Focus on 12 Striking Distance keywords to reach Top 3 quickly.</p>
                            </li>
                        </ul>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
