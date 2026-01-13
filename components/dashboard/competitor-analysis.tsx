import { getCompetitorAnalysis } from '@/lib/data-service'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

export async function CompetitorAnalysis({ importId }: { importId: string }) {
    const competitors = await getCompetitorAnalysis(importId)

    return (
        <Card>
            <CardHeader>
                <CardTitle>Competitor Benchmark</CardTitle>
                <CardDescription>Market Share and Performance Comparison</CardDescription>
            </CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Domain</TableHead>
                            <TableHead>Share of Voice</TableHead>
                            <TableHead>Visibility</TableHead>
                            <TableHead>Top 10 Keywords</TableHead>
                            <TableHead>Avg Position</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {competitors.map((comp) => (
                            <TableRow key={comp.domain}>
                                <TableCell className="font-medium">{comp.domain}</TableCell>
                                <TableCell>
                                    <div className="flex items-center gap-2">
                                        <span className="w-12 text-right">{comp.sov.toFixed(1)}%</span>
                                        <div className="h-2 w-24 bg-secondary rounded-full overflow-hidden">
                                            <div className="h-full bg-primary" style={{ width: `${Math.min(comp.sov, 100)}%` }} />
                                        </div>
                                    </div>
                                </TableCell>
                                <TableCell>{comp.visibility.toFixed(0)}</TableCell>
                                <TableCell>{comp.top10}</TableCell>
                                <TableCell>{comp.avgPos.toFixed(1)}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    )
}
