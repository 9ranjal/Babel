// Minimal, robust SSE parser for fetch Response streams
export async function* parseSSE(response: Response) {
  const body = (response as any).body;
  if (!body || !body.getReader) {
    throw new Error('Response body is not a readable stream');
  }
  const reader = body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buf = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });

    let idx;
    while ((idx = buf.indexOf('\n\n')) !== -1) {
      const raw = buf.slice(0, idx);
      buf = buf.slice(idx + 2);

      let eventType: string | null = null;
      let dataLine = '';

      for (const line of raw.split('\n')) {
        if (line.startsWith('event:')) eventType = line.replace('event:', '').trim();
        if (line.startsWith('data:')) dataLine += line.replace('data:', '').trim();
      }

      try {
        const parsed = dataLine ? JSON.parse(dataLine) : {};
        const type = (eventType || (parsed && parsed.type)) || null;
        yield { type, ...parsed } as any;
      } catch {
        yield { type: eventType || 'message', raw: dataLine } as any;
      }
    }
  }
}

export type StreamEvent =
  | { type: 'start'; [key: string]: any }
  | { type: 'chunk'; chunk: string }
  | { type: 'delta'; text?: string; delta?: string }
  | { type: 'result'; data: any }
  | { type: 'tutor_response'; data: any }
  | { type: 'phase'; phase?: string; data?: any }
  | { type: 'citations_ready'; citations?: any[] }
  | { type: 'complete'; data?: any }
  | { type: 'error'; error?: string; data?: any }
  | { content: string };

