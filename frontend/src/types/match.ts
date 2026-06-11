export interface JobMatch {
  job_id: string
  title: string
  company: string
  location: string
  remote: string
  match_score: number
  reasoning: string
  highlight_bullet: string
}

export type StreamEventType = 'status' | 'match' | 'done' | 'error'

export interface StatusEvent {
  stage: 'parsing' | 'embedding' | 'retrieving' | 'ranking'
}

export interface DoneEvent {
  total: number
  duration_ms: number
  cache_hit?: boolean
}

export interface ErrorEvent {
  message: string
}
