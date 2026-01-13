'use client'

import dynamic from 'next/dynamic'
import { Button } from '@/components/ui/button'
import { FileDown } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { ExecutiveSummaryData } from '@/lib/data-service'

// Dynamically import PDF Download Link to avoid SSR issues
const PDFDownloadLink = dynamic(
    () => import('@react-pdf/renderer').then((mod) => mod.PDFDownloadLink),
    { ssr: false, loading: () => <Button variant="outline" disabled>Loading PDF...</Button> }
)

import { ExecutivePdf } from './pdf-view'

export function PdfExportButton({ data, period }: { data: ExecutiveSummaryData, period: string }) {
    const [isClient, setIsClient] = useState(false)

    useEffect(() => {
        setIsClient(true)
    }, [])

    if (!isClient) return <Button variant="outline" disabled>Preparing...</Button>

    return (
        <PDFDownloadLink document={<ExecutivePdf data={data} period={period} project="SEO Dashboard" />} fileName={`report-${period}.pdf`}>
            {/* Function As Child to handle loading state from PDF lib */}
            {({ blob, url, loading, error }) => (
                <Button variant="outline" disabled={loading}>
                    <FileDown className="mr-2 h-4 w-4" />
                    {loading ? 'Generating...' : 'Export PDF'}
                </Button>
            )}
        </PDFDownloadLink>
    )
}
