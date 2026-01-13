import { getOpportunities } from '@/lib/data-service'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { ExternalLink } from 'lucide-react'

export async function OpportunitiesView({ importId, domain }: { importId: string, domain: string }) {
    const opportunities = await getOpportunities(importId, domain)
    const quickWins = opportunities.filter(o => o.type === 'Quick Win')
    const strikingDistance = opportunities.filter(o => o.type === 'Striking Distance')

    return (
        <div className="space-y-6">
            <Card className="border-green-100 bg-green-50/20">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        🚀 Quick Wins
                        <Badge variant="secondary" className="ml-2">{quickWins.length}</Badge>
                    </CardTitle>
                    <CardDescription>Keywords in positions 4-10 with high search volume. Optimizing these can yield fast traffic gains.</CardDescription>
                </CardHeader>
                <CardContent>
                    <OpportunityTable data={quickWins.slice(0, 10)} />
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        🎯 Striking Distance
                        <Badge variant="secondary" className="ml-2">{strikingDistance.length}</Badge>
                    </CardTitle>
                    <CardDescription>Keywords in positions 11-20. Promote these to page 1.</CardDescription>
                </CardHeader>
                <CardContent>
                    <OpportunityTable data={strikingDistance.slice(0, 10)} />
                </CardContent>
            </Card>
        </div>
    )
}

function OpportunityTable({ data }: { data: any[] }) {
    if (data.length === 0) return <div className="text-sm text-muted-foreground">No opportunities found in this category.</div>

    return (
        <Table>
            <TableHeader>
                <TableRow>
                    <TableHead>Keyword</TableHead>
                    <TableHead>Pos</TableHead>
                    <TableHead>Volume</TableHead>
                    <TableHead>Difficulty</TableHead>
                    <TableHead>URL</TableHead>
                    <TableHead>Action</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {data.map((row, i) => (
                    <TableRow key={i}>
                        <TableCell className="font-medium">{row.keyword}</TableCell>
                        <TableCell>{row.position}</TableCell>
                        <TableCell>{row.volume?.toLocaleString() ?? '-'}</TableCell>
                        <TableCell>
                            <Badge variant={row.difficulty > 60 ? "destructive" : row.difficulty > 30 ? "default" : "secondary"}>
                                {row.difficulty ?? 'N/A'}
                            </Badge>
                        </TableCell>
                        <TableCell className="max-w-[200px] truncate text-xs text-muted-foreground" title={row.url}>
                            {row.url}
                        </TableCell>
                        <TableCell>
                            <div className="flex items-center text-xs text-blue-600 font-medium">
                                Optimize Content
                            </div>
                        </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    )
}
