import { resolveApiUrl } from './config'

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(await res.text())
  return (await res.json()) as T
}

export async function upload(file: File): Promise<{ document_id: string }> {
  const fd = new FormData()
  fd.append('file', file)
  const url = resolveApiUrl('/upload')
  if (import.meta.env.DEV) {
    console.debug('[api] upload ->', url)
  }
  const res = await fetch(url, { method: 'POST', body: fd })
  return json(res)
}

export async function getDocument(id: string) {
  const res = await fetch(resolveApiUrl(`/documents/${id}`))
  return json<any>(res)
}

export async function getDocumentStatus(id: string): Promise<{ status: string }> {
  const res = await fetch(resolveApiUrl(`/documents/${id}/status`))
  return json<{ status: string }>(res)
}

export async function listClauses(id: string) {
  const res = await fetch(resolveApiUrl(`/documents/${id}/clauses`))
  return json<any[]>(res)
}

export async function getClause(id: string) {
  const res = await fetch(resolveApiUrl(`/clauses/${id}`))
  return json<any>(res)
}

export async function analyzeClause(id: string) {
  const res = await fetch(resolveApiUrl(`/clauses/${id}/analyze`), { method: 'POST' })
  return json<any>(res)
}

export async function redraftClause(id: string) {
  const res = await fetch(resolveApiUrl(`/clauses/${id}/redraft`), { method: 'POST' })
  return json<any>(res)
}


