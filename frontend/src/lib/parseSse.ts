export interface SseMessage {
  event: string
  data: string
}

export function parseSseChunk(buffer: string): { messages: SseMessage[]; remainder: string } {
  const messages: SseMessage[] = []
  const parts = buffer.split('\n\n')
  const remainder = parts.pop() ?? ''

  for (const part of parts) {
    if (!part.trim()) continue

    let event = 'message'
    const dataLines: string[] = []

    for (const line of part.split('\n')) {
      if (line.startsWith('event:')) {
        event = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).trim())
      }
    }

    if (dataLines.length > 0) {
      messages.push({ event, data: dataLines.join('\n') })
    }
  }

  return { messages, remainder }
}
