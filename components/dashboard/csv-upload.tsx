'use client'

import { useState } from 'react'
import { uploadCSV } from '@/lib/actions'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Loader2 } from 'lucide-react'

export function CsvUpload({ projectId }: { projectId: string }) {
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState<{ success?: boolean; error?: string; count?: number } | null>(null)

    async function handleSubmit(formData: FormData) {
        setLoading(true)
        setResult(null)
        const res = await uploadCSV(projectId, formData)
        setResult(res as any)
        setLoading(false)
    }

    return (
        <div className="p-4 border rounded-lg bg-card text-card-foreground shadow-sm max-w-md">
            <h3 className="text-lg font-semibold mb-4">Import Monthly CSV</h3>
            <form action={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                    <Label htmlFor="month">Month (YYYY-MM)</Label>
                    <Input type="month" name="month" required />
                </div>

                <div className="space-y-2">
                    <Label htmlFor="file">CSV File</Label>
                    <Input type="file" name="file" accept=".csv" required />
                </div>

                <Button type="submit" disabled={loading} className="w-full">
                    {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : 'Import Data'}
                </Button>
            </form>

            {result?.error && (
                <Alert variant="destructive" className="mt-4">
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{result.error}</AlertDescription>
                </Alert>
            )}

            {result?.success && (
                <Alert className="mt-4 bg-green-50 text-green-900 border-green-200">
                    <AlertTitle>Success</AlertTitle>
                    <AlertDescription>Imported {result.count} keywords successfully.</AlertDescription>
                </Alert>
            )}
        </div>
    )
}
