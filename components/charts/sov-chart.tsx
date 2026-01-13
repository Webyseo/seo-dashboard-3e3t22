'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface SovChartProps {
    data: {
        month: string
        [key: string]: string | number // domain: sov
    }[]
    domains: string[]
}

export function SovChart({ data, domains }: SovChartProps) {
    const colors = ['#2563eb', '#16a34a', '#dc2626', '#d97706', '#9333ea']

    return (
        <Card className="col-span-2">
            <CardHeader>
                <CardTitle>Share of Voice History</CardTitle>
            </CardHeader>
            <CardContent className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="month" />
                        <YAxis unit="%" />
                        <Tooltip />
                        <Legend />
                        {domains.map((domain, i) => (
                            <Line
                                key={domain}
                                type="monotone"
                                dataKey={domain}
                                stroke={colors[i % colors.length]}
                                strokeWidth={2}
                                dot={{ r: 4 }}
                            />
                        ))}
                    </LineChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    )
}
