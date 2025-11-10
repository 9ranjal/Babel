import { getClause } from './api'
import { resolveApiUrl } from './config'
import { enqueueAssistantMessage, enqueueUserMessage } from './chatBus'

function snippet(text: string | undefined, max = 500): string {
  if (!text) return ''
  if (text.length <= max) return text
  return text.slice(0, max) + '…'
}

export async function analyzeClauseInChat(clauseId: string) {
  const clause = await getClause(clauseId)
  const title = clause?.title || clause?.clause_key || 'Clause'
  const text = clause?.text || ''
  const leverage = clause?.leverage_json || { investor: 0.6, founder: 0.4 }
  const investorPct = Math.round((leverage.investor ?? 0.6) * 100)
  const founderPct = Math.round((leverage.founder ?? 0.4) * 100)

  // 1b: enqueue a user-style context message first
  const userMsg =
    `Analyzing: ${title}\n\n` +
    `${snippet(text)}\n\n` +
    `Leverage: investor ${investorPct}%, founder ${founderPct}%\n` +
    `Using BATNA v1 bands`
  enqueueUserMessage(userMsg)

  // Call copilot reasoned analysis endpoint
  const payload = {
    clause_key: clause?.clause_key || '',
    clause_title: title,
    clause_text: text,
    attributes: {}, // optional; regex-derived attrs can be added later
    leverage,
  }
  const res = await fetch(resolveApiUrl('/copilot/analyze-clause'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const errText = await res.text().catch(() => 'Unknown error')
    enqueueAssistantMessage(`Sorry, I couldn't analyze that clause. (${res.status}) ${errText}`)
    return
  }
  const data = (await res.json()) as { analysis?: string }
  const analysis = data?.analysis || 'No analysis produced.'
  enqueueAssistantMessage(analysis)
}



