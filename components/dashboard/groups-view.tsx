import { getGroupAnalysisWithDomain } from '@/lib/data-service'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

export async function GroupsView({ importId, domain }: { importId: string, domain: string }) {
    const groups = await getGroupAnalysisWithDomain(importId, domain)

    return (
        <Card>
            <CardHeader><CardTitle>Group Performance</CardTitle></CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Group Name</TableHead>
                            <TableHead>Keywords</TableHead>
                            <TableHead>Total Visibility</TableHead>
                            <TableHead>Avg Position</TableHead>
                            <TableHead>Top 10 Count</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {groups.map(g => (
                            <TableRow key={g.name}>
                                <TableCell className="font-medium">{g.name}</TableCell>
                                <TableCell>{g.count}</TableCell>
                                <TableCell>{g.totalVis.toFixed(1)}</TableCell>
                                <TableCell>{g.avgPos.toFixed(1)}</TableCell>
                                <TableCell>{g.top10}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    )
}
