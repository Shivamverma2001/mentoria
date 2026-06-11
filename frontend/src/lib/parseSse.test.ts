import { describe, expect, it } from 'vitest'
import { parseSseChunk } from './parseSse'

describe('parseSseChunk', () => {
  it('parses a complete SSE message', () => {
    const chunk = 'event: status\ndata: {"stage":"parsing"}\n\n'
    const { messages, remainder } = parseSseChunk(chunk)
    expect(messages).toHaveLength(1)
    expect(messages[0].event).toBe('status')
    expect(JSON.parse(messages[0].data)).toEqual({ stage: 'parsing' })
    expect(remainder).toBe('')
  })

  it('buffers partial messages', () => {
    const part1 = 'event: match\ndata: {"job_id":'
    const { messages: m1, remainder: r1 } = parseSseChunk(part1)
    expect(m1).toHaveLength(0)
    expect(r1).toBe(part1)

    const part2 = '"job_001"}\n\n'
    const { messages: m2 } = parseSseChunk(r1 + part2)
    expect(m2).toHaveLength(1)
    expect(m2[0].event).toBe('match')
  })

  it('parses multiple events in one chunk', () => {
    const chunk =
      'event: status\ndata: {"stage":"ranking"}\n\n' +
      'event: match\ndata: {"job_id":"job_005","title":"Dev","company":"M","location":"X","remote":"hybrid","match_score":90,"reasoning":"Good fit for you.","highlight_bullet":"Built agents"}\n\n'
    const { messages } = parseSseChunk(chunk)
    expect(messages).toHaveLength(2)
    expect(messages[1].event).toBe('match')
  })
})
