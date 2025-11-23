import { resolveApiUrl } from './config'

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text()
    console.error('[api] request failed', { url: res.url, status: res.status, body })
    throw new Error(body || `HTTP ${res.status}`)
  }
  return (await res.json()) as T
}

export async function upload(file: File): Promise<{ document_id: string; requeued?: boolean }> {
  const fd = new FormData()
  fd.append('file', file)
  const url = resolveApiUrl('/upload')
  if (import.meta.env.DEV) {
    console.debug('[api] upload ->', url)
  }
  const res = await fetch(url, { method: 'POST', body: fd })
  const result = await json<{ document_id: string; requeued?: boolean }>(res)
  if (import.meta.env.DEV) {
    console.debug('[api] upload <-', { documentId: result.document_id, requeued: result.requeued })
  }
  return result
}

export async function getDocument(id: string) {
  const res = await fetch(resolveApiUrl(`/documents/${id}`))
  const doc = await json<any>(res)
  if (import.meta.env.DEV) {
    console.debug('[api] getDocument', { id, status: doc?.status, clauseCount: doc?.clauses?.length })
  }
  return doc
}

export async function getDocumentStatus(id: string): Promise<{ status: string }> {
  const res = await fetch(resolveApiUrl(`/documents/${id}/status`))
  const status = await json<{ status: string }>(res)
  if (import.meta.env.DEV) {
    console.debug('[api] getDocumentStatus', { id, status: status.status })
  }
  return status
}

export async function listClauses(id: string) {
  const res = await fetch(resolveApiUrl(`/documents/${id}/clauses`))
  const clauses = await json<any[]>(res)
  if (import.meta.env.DEV) {
    console.debug('[api] listClauses', { id, count: clauses.length })
  }
  return clauses
}

export async function getClause(id: string) {
  const res = await fetch(resolveApiUrl(`/clauses/${id}`))
  const clause = await json<any>(res)
  if (import.meta.env.DEV) {
    console.debug('[api] getClause', { id, hasText: Boolean(clause?.text) })
  }
  return clause
}

export async function analyzeClause(id: string, reasoned: boolean = false) {
  const url = reasoned
    ? resolveApiUrl(`/clauses/${id}/analyze?reasoned=true`)
    : resolveApiUrl(`/clauses/${id}/analyze`)
  const res = await fetch(url, { method: 'POST' })
  const analysis = await json<any>(res)
  if (import.meta.env.DEV) {
    console.debug('[api] analyzeClause', { id, reasoned, band: analysis?.band_name })
  }
  return analysis
}

export async function redraftClause(id: string) {
  const res = await fetch(resolveApiUrl(`/clauses/${id}/redraft`), { method: 'POST' })
  const redraft = await json<any>(res)
  if (import.meta.env.DEV) {
    console.debug('[api] redraftClause', { id, hasRedraft: Boolean(redraft?.redraft_text) })
  }
  return redraft
}

export async function generateTermSheet(nlInput: string) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 150000); // 150 second timeout
  
  try {
    const res = await fetch(resolveApiUrl('/ts-generator/generate'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nl_input: nlInput }),
      signal: controller.signal,
    })
    clearTimeout(timeoutId);
    const result = await json<{
      term_sheet: string
      deal_config: Record<string, any>
      validation_errors: string[]
      clarification_questions: string[] | null
    }>(res)
    if (import.meta.env.DEV) {
      console.debug('[api] generateTermSheet', { 
        hasTermSheet: Boolean(result?.term_sheet),
        errors: result?.validation_errors?.length || 0,
      })
    }
    return result
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Request timed out. The term sheet generation is taking longer than expected. Please try again.');
    }
    throw error;
  }
}


