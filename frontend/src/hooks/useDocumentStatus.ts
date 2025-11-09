import { useEffect, useRef, useState } from 'react'
import { getDocumentStatus } from '../lib/api'

export function useDocumentStatus(documentId: string | null | undefined, intervalMs = 1000) {
  const [status, setStatus] = useState<string | null>(null)
  const timerRef = useRef<number | null>(null)

  useEffect(() => {
    if (!documentId) return
    let cancelled = false
    async function tick() {
      try {
        const res = await getDocumentStatus(documentId)
        if (!cancelled) setStatus(res.status)
      } catch {
        // ignore
      }
    }
    void tick()
    timerRef.current = window.setInterval(() => void tick(), intervalMs)
    return () => {
      cancelled = true
      if (timerRef.current) window.clearInterval(timerRef.current)
    }
  }, [documentId, intervalMs])

  return status
}


