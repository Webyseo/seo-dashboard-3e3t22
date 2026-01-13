'use server'

import { prisma } from '@/lib/db'
import { parseCSV } from '@/lib/csv-parser'
import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'

export async function createProject(formData: FormData) {
    const name = formData.get('name') as string
    if (!name) return { error: 'Project name is required' }

    const project = await prisma.project.create({
        data: { name }
    })

    redirect(`/dashboard/${project.id}`)
}

export async function uploadCSV(projectId: string, formData: FormData) {
    const file = formData.get('file') as File
    const monthLabel = formData.get('month') as string

    if (!file || !monthLabel) {
        return { error: 'File and Month are required' }
    }

    try {
        const text = await file.text()
        const { rows, domains, error } = await parseCSV(text)

        if (error) return { error }
        if (!rows.length) return { error: 'No valid rows found' }

        // Transactional Insert
        await prisma.$transaction(async (tx) => {
            // 1. Create Import Record
            const importRecord = await tx.import.create({
                data: {
                    projectId,
                    monthLabel,
                    filename: file.name
                }
            })

            // 2. Upsert Keywords and Prepare Data
            // SQLite/Prisma doesn't support "createMany" with "skipDuplicates" nicely for relations sometimes
            // So we iterate. For performance on thousands of rows, we might optimize this later.
            // But connectOrCreate is safe.

            for (const row of rows) {
                // Find or Create Keyword
                let keyword = await tx.keyword.findUnique({
                    where: {
                        projectId_text: {
                            projectId,
                            text: row.keyword
                        }
                    }
                })

                if (!keyword) {
                    keyword = await tx.keyword.create({
                        data: {
                            projectId,
                            text: row.keyword,
                            group: row.group
                        }
                    })
                } else if (row.group && keyword.group !== row.group) {
                    // Optional: Update group if new one provided
                    // await tx.keyword.update(...)
                }

                // 3. Create Metric
                await tx.keywordMetric.create({
                    data: {
                        importId: importRecord.id,
                        keywordId: keyword.id,
                        difficulty: row.difficulty,
                        volume: row.searches,
                        impressions: row.impressions,
                        ctr: row.ctr,
                        competition: row.competition,
                        cpcAvg: row.cpcAvg,
                        cpcMin: row.cpcMin,
                        cpcMax: row.cpcMax,
                        trend3m: row.trend3m
                    }
                })

                // 4. Create Rankings
                const rankingInserts = Object.entries(row.rankings).map(([domain, data]) => ({
                    importId: importRecord.id,
                    keywordId: keyword.id,
                    domain,
                    visibility: data.visibility,
                    position: data.position,
                    outOfTop20: data.outOfTop20,
                    url: data.url
                }))

                if (rankingInserts.length > 0) {
                    await tx.domainRanking.createMany({
                        data: rankingInserts
                    })
                }
            }
        }, {
            maxWait: 10000, // 10s
            timeout: 60000  // 60s
        })

        revalidatePath(`/dashboard/${projectId}`)
        return { success: true, count: rows.length }

    } catch (err: any) {
        console.error(err)
        return { error: 'Database import failed: ' + err.message }
    }
}
