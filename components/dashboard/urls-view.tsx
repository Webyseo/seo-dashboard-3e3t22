import { getUrlAnalysis } from '@/lib/data-service'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

export async function UrlsView({ importId, domain }: { importId: string, domain: string }) {
    const urls = await getUrlAnalysis(importId, domain)

    return (
        <Card>
            <CardHeader><CardTitle>Pages (URLs)</CardTitle></CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>URL</TableHead>
                            <TableHead>Keywords</TableHead>
                            <TableHead>Visibility</TableHead>
                            <TableHead>Top 10 Keywords</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {urls.slice(0, 50).map((u, i) => (
                            <TableRow key={i}>
                                <TableCell className="max-w-[300px] truncate" title={u.url}>{u.url}</TableCell>
                                <TableCell>{u.count}</TableCell>
                                <TableCell>{u.vis.toFixed(1)}</TableCell>
                                <TableCell>{u.top10}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    )
}
