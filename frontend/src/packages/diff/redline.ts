function escapeHtml(input: string): string {
  return input
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

export function getRedlineMarkup(
  _spans: Record<string, any> | undefined,
  _clauseId: string | undefined,
  redraftText: string | undefined,
): string {
  if (!redraftText) {
    return '';
  }

  return `<pre style="white-space:pre-wrap;font-family:'SN Pro',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:0.875rem;line-height:1.5;color:var(--ink-700);">${escapeHtml(
    redraftText,
  )}</pre>`;
}


