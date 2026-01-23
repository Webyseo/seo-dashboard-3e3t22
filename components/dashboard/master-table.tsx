'use client'

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { MasterEvolutionRow } from "@/lib/data-service"
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts'
import { ArrowUp, ArrowDown, Minus, ExternalLink } from 'lucide-react'

interface MasterTableProps {
    data: MasterEvolutionRow[]
    onSelectKeyword?: (keyword: string) => void
}

export function MasterTable({ data, onSelectKeyword }: MasterTableProps) {
    return (
        <div className="rounded-md border">
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead className="w-[300px]">Keyword</TableHead>
                        <TableHead>Intent</TableHead>
                        <TableHead className="text-right">Pos</TableHead>
                        <TableHead className="text-right">Delta</TableHead>
                        <TableHead className="w-[100px]">Trend (3m)</TableHead>
                        <TableHead className="text-right">Value</TableHead>
                        <TableHead>Action</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {data.map((row) => (
                        <TableRow
                            key={row.keyword}
                            className="cursor-pointer hover:bg-muted/50"
                            onClick={() => onSelectKeyword?.(row.keyword)}
                        >
                            <TableCell className="font-medium">
                                <div className="flex flex-col">
                                    <span>{row.keyword}</span>
                                    {row.url && (
                                        <a href={row.url} target="_blank" rel="noopener noreferrer" className="text-xs text-muted-foreground flex items-center hover:underline" onClick={(e) => e.stopPropagation()}>
                                            {new URL(row.url).pathname} <ExternalLink className="h-3 w-3 ml-1" />
                                        </a>
                                    )}
                                </div>
                            </TableCell>
                            <TableCell>
                                <IntentBadge intent={row.intent} />
                            </TableCell>
                            <TableCell className="text-right font-bold">
                                {row.position > 100 ? '-' : row.position}
                            </TableCell>
                            <TableCell className="text-right">
                                <DeltaIndicator delta={row.delta} />
                            </TableCell>
                            <TableCell>
                                <div className="h-[30px] w-[80px]">
                                    <Sparkline data={row.trend} />
                                </div>
                            </TableCell>
                            <TableCell className="text-right text-green-600 font-medium">
                                {row.value > 0 ? `+${row.value.toFixed(2)}€` : '-'}
                            </TableCell>
                            <TableCell>
                                <ActionBadge action={row.action} />
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    )
}

function IntentBadge({ intent }: { intent: string }) {
    let variant: "default" | "secondary" | "destructive" | "outline" = "outline"
    if (intent === 'Commercial') variant = "default"
    if (intent === 'Informational') variant = "secondary"

    return <Badge variant={variant}>{intent}</Badge>
}

function DeltaIndicator({ delta }: { delta: number }) {
    if (delta > 0) return <span className="text-green-600 flex items-center justify-end"><ArrowUp className="h-4 w-4 mr-1" /> {delta}</span>
    if (delta < 0) return <span className="text-red-500 flex items-center justify-end"><ArrowDown className="h-4 w-4 mr-1" /> {Math.abs(delta)}</span>
    return <span className="text-muted-foreground flex items-center justify-end"><Minus className="h-4 w-4 mr-1" /></span>
}

function ActionBadge({ action }: { action: string }) {
    // Dynamic styles based on action content?
    return <span className="text-xs font-medium px-2 py-1 rounded-full bg-slate-100 text-slate-800 border">{action}</span>
}

function Sparkline({ data }: { data: number[] }) {
    // Transform array [10, 5, 2] to [{val: 10, i:0}, ...]
    // Note: data is [Oldest, Middle, Newest]
    // We want to reverse Y axis so lower rank (1) is higher visually.
    const chartData = data.map((val, i) => ({ i, val: val === 0 ? null : val }))

    return (
        <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
                <YAxis domain={['dataMin', 'dataMax']} reversed hide />
                <Line
                    type="monotone"
                    dataKey="val"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                />
            </LineChart>
        </ResponsiveContainer>
    )
}
