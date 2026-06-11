import { apiUrl } from '../lib/apiBase'
import { parseSseChunk } from '../lib/parseSse'
import type { DoneEvent, ErrorEvent, JobMatch, StatusEvent } from '../types/match'

export type MatchStreamHandlers = {
  onStatus?: (event: StatusEvent) => void
  onMatch?: (match: JobMatch) => void
  onDone?: (event: DoneEvent) => void
  onError?: (event: ErrorEvent) => void
}

async function readMatchStream(response: Response, handlers: MatchStreamHandlers): Promise<void> {
  if (!response.ok) {
    let message = `Match request failed (${response.status})`
    try {
      const body = await response.json()
      message = body.detail ?? message
    } catch {
      // ignore JSON parse errors
    }
    handlers.onError?.({ message })
    return
  }

  if (!response.body) {
    handlers.onError?.({ message: 'No response stream from server' })
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const { messages, remainder } = parseSseChunk(buffer)
    buffer = remainder

    for (const message of messages) {
      const payload = JSON.parse(message.data) as unknown

      switch (message.event) {
        case 'status':
          handlers.onStatus?.(payload as StatusEvent)
          break
        case 'match':
          handlers.onMatch?.(payload as JobMatch)
          break
        case 'done':
          handlers.onDone?.(payload as DoneEvent)
          break
        case 'error':
          handlers.onError?.(payload as ErrorEvent)
          break
        default:
          break
      }
    }
  }
}

export async function streamMatchFromText(
  resumeText: string,
  handlers: MatchStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(apiUrl('/api/match/stream/json'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resume_text: resumeText }),
    signal,
  })
  await readMatchStream(response, handlers)
}

export async function streamMatchFromPdf(
  file: File,
  handlers: MatchStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const form = new FormData()
  form.append('resume_file', file)

  const response = await fetch(apiUrl('/api/match/stream'), {
    method: 'POST',
    body: form,
    signal,
  })
  await readMatchStream(response, handlers)
}
