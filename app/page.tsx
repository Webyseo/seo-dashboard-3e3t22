import { prisma } from '@/lib/db'
import { createProject } from '@/lib/actions'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import Link from 'next/link'
import { Plus } from 'lucide-react'

export const dynamic = 'force-dynamic'

export default async function Home() {
  const projects = await prisma.project.findMany({
    orderBy: { createdAt: 'desc' }
  })

  return (
    <main className="container mx-auto py-10 px-4">
      <h1 className="text-4xl font-bold mb-8 text-slate-800">SEO Executive Dashboard</h1>

      <div className="grid md:grid-cols-2 gap-8">
        <section>
          <h2 className="text-2xl font-semibold mb-4">Your Projects</h2>
          <div className="grid gap-4">
            {projects.length === 0 && (
              <p className="text-muted-foreground">No projects found. Create one to get started.</p>
            )}
            {projects.map(p => (
              <Link key={p.id} href={`/dashboard/${p.id}`} className="block">
                <Card className="hover:bg-slate-50 transition">
                  <CardHeader>
                    <CardTitle>{p.name}</CardTitle>
                    <CardDescription>Created: {p.createdAt.toLocaleDateString()}</CardDescription>
                  </CardHeader>
                </Card>
              </Link>
            ))}
          </div>
        </section>

        <section>
          <Card>
            <CardHeader>
              <CardTitle>Create New Project</CardTitle>
              <CardDescription>Start managing SEO data for a new client</CardDescription>
            </CardHeader>
            <CardContent>
              <form action={createProject as any} className="flex gap-4">
                <Input name="name" placeholder="Project Name (e.g. Radiofonics)" required />
                <Button type="submit">
                  <Plus className="mr-2 h-4 w-4" /> Create
                </Button>
              </form>
            </CardContent>
          </Card>
        </section>
      </div>
    </main>
  )
}
