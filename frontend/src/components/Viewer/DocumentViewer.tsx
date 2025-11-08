import React, { useEffect, useRef } from 'react'

type HtmlPage = { index: number; html: string }

export function DocumentViewer({
  htmlPages,
  highlightSpanId,
}: {
  htmlPages: HtmlPage[]
  highlightSpanId?: string
}) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!highlightSpanId || !containerRef.current) return
    const el = containerRef.current.querySelector(`#${CSS.escape(highlightSpanId)}`)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      el.classList.add('ring-2', 'ring-blue-500')
      const t = setTimeout(() => el.classList.remove('ring-2', 'ring-blue-500'), 1200)
      return () => clearTimeout(t)
    }
  }, [highlightSpanId])

  return (
    <div ref={containerRef} className="p-4 space-y-6">
      {htmlPages.map((p) => (
        <div key={p.index} className="prose max-w-none" dangerouslySetInnerHTML={{ __html: p.html }} />
      ))}
    </div>
  )
}


