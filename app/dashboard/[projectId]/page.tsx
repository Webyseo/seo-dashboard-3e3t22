import { prisma } from '@/lib/db'
import { CsvUpload } from '@/components/dashboard/csv-upload'
import { ExecutiveSummary } from '@/components/dashboard/executive-summary'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button' // Verified import
import { CompetitorAnalysis } from '@/components/dashboard/competitor-analysis'
import { RankingsContainer } from '@/components/dashboard/rankings-container'
import { OpportunitiesView } from '@/components/dashboard/opportunities-view'
import { GroupsView } from '@/components/dashboard/groups-view'
import { UrlsView } from '@/components/dashboard/urls-view'
import Link from 'next/link'
import { ArrowLeft, Calendar } from 'lucide-react'
import { redirect } from 'next/navigation'

export default async function DashboardPage({
    params,
    searchParams
}: {
    params: Promise<{ projectId: string }>,
    searchParams: Promise<{ month?: string, domain?: string }>
}) {
    const { projectId } = await params
    const resolvedSearchParams = await searchParams

    const project = await prisma.project.findUnique({
        where: { id: projectId },
        include: { imports: { orderBy: { monthLabel: 'desc' } } }
    })

    if (!project) return <div>Project not found</div>

    const imports = project.imports
    const hasData = imports.length > 0

    // Determine current import based on ?month=... or default to latest
    const selectedMonth = resolvedSearchParams.month
    const currentImport = selectedMonth
        ? imports.find(i => i.monthLabel === selectedMonth)
        : imports[0]

    const currentDomain = resolvedSearchParams.domain || 'radiofonics.com'

    // If we have data but no valid import selected (e.g. invalid month param), default to first
    if (hasData && !currentImport && !selectedMonth) {
        // Already handled by default, but if selectedMonth provided but not found:
    }

    return (
        <div className="min-h-screen bg-slate-50">
            <header className="bg-white border-b sticky top-0 z-10">
                <div className="container mx-auto py-4 px-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/" className="text-sm text-muted-foreground hover:text-foreground">
                            <ArrowLeft className="h-4 w-4" />
                        </Link>
                        <h1 className="text-xl font-bold">{project.name}</h1>
                        <Badge variant="outline">{imports.length} Imports</Badge>
                    </div>

                    <div className="flex items-center gap-4">
                        {/* Global Filters */}
                        {hasData && (
                            <div className="flex items-center gap-2">
                                <Calendar className="h-4 w-4 text-muted-foreground" />
                                <form className="flex item-center">
                                    {/* Basic selection via links/navigation for MVP simplicity or client component for interactivity */}
                                    <Select defaultValue={currentImport?.monthLabel} >
                                        <SelectTrigger className="w-[180px]">
                                            <SelectValue placeholder="Select Month" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {imports.map(imp => (
                                                <Link key={imp.id} href={`/dashboard/${projectId}?month=${imp.monthLabel}`} passHref legacyBehavior={false}>
                                                    <SelectItem value={imp.monthLabel}>{imp.monthLabel}</SelectItem>
                                                </Link>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </form>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            <main className="container mx-auto py-8 px-4 space-y-8">
                {!hasData ? (
                    <div className="flex flex-col items-center justify-center py-20 bg-white rounded-lg border border-dashed">
                        <h2 className="text-2xl font-bold mb-4">Welcome to your Dashboard</h2>
                        <p className="text-muted-foreground mb-8">Upload your first monthly CSV report to see the analytics.</p>
                        <CsvUpload projectId={project.id} />
                    </div>
                ) : (
                    <Tabs defaultValue="overview" className="space-y-4">
                        <div className="flex justify-between items-center overflow-x-auto">
                            <TabsList>
                                <TabsTrigger value="overview">Executive Summary</TabsTrigger>
                                <TabsTrigger value="competition">Competition</TabsTrigger>
                                <TabsTrigger value="rankings">Rankings</TabsTrigger>
                                <TabsTrigger value="groups">Groups</TabsTrigger>
                                <TabsTrigger value="urls">URLs</TabsTrigger>
                                <TabsTrigger value="opportunities">Opportunities</TabsTrigger>
                                <TabsTrigger value="data">Data Quality</TabsTrigger>
                            </TabsList>
                        </div>

                        <TabsContent value="overview">
                            {currentImport ? (
                                <ExecutiveSummary importId={currentImport.id} domain={currentDomain} />
                            ) : (
                                <div className="p-4">Select a month to view data.</div>
                            )}
                        </TabsContent>

                        <TabsContent value="competition">
                            {currentImport ? (
                                <CompetitorAnalysis importId={currentImport.id} />
                            ) : null}
                        </TabsContent>

                        <TabsContent value="rankings">
                            {currentImport ? (
                                <RankingsContainer importId={currentImport.id} domain={currentDomain} />
                            ) : null}
                        </TabsContent>

                        <TabsContent value="opportunities">
                            {currentImport ? (
                                <OpportunitiesView importId={currentImport.id} domain={currentDomain} />
                            ) : null}
                        </TabsContent>

                        <TabsContent value="groups">
                            {currentImport ? (
                                <GroupsView importId={currentImport.id} domain={currentDomain} />
                            ) : null}
                        </TabsContent>

                        <TabsContent value="urls">
                            {currentImport ? (
                                <UrlsView importId={currentImport.id} domain={currentDomain} />
                            ) : null}
                        </TabsContent>

                        <TabsContent value="data">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                <div className="md:col-span-1">
                                    <CsvUpload projectId={project.id} />
                                </div>
                                <div className="md:col-span-2">
                                    <Card>
                                        <CardHeader><CardTitle>Import History</CardTitle></CardHeader>
                                        <CardContent>
                                            <ul className="space-y-4">
                                                {imports.map(imp => (
                                                    <li key={imp.id} className="flex justify-between items-center border-b pb-2 last:border-0">
                                                        <div>
                                                            <p className="font-medium">{imp.monthLabel}</p>
                                                            <p className="text-xs text-muted-foreground">{imp.filename}</p>
                                                        </div>
                                                        <Badge variant="secondary">{imp.importedAt.toLocaleDateString()}</Badge>
                                                    </li>
                                                ))}
                                            </ul>
                                        </CardContent>
                                    </Card>
                                </div>
                            </div>
                        </TabsContent>
                    </Tabs>
                )}
            </main>
        </div>
    )
}
