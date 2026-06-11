import { useCallback, useRef, useState } from 'react'
import { streamMatchFromPdf, streamMatchFromText } from '../api/matchStream'
import type { DoneEvent, JobMatch, StatusEvent } from '../types/match'

export type MatchPhase = 'idle' | 'streaming' | 'done' | 'error'

const STAGE_LABELS: Record<StatusEvent['stage'], string> = {
  parsing: 'Parsing resume…',
  embedding: 'Generating embeddings…',
  retrieving: 'Finding similar jobs…',
  ranking: 'Ranking with AI…',
}

export function useJobMatch() {
  const [phase, setPhase] = useState<MatchPhase>('idle')
  const [stageLabel, setStageLabel] = useState<string | null>(null)
  const [matches, setMatches] = useState<JobMatch[]>([])
  const [doneMeta, setDoneMeta] = useState<DoneEvent | null>(null)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const reset = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setPhase('idle')
    setStageLabel(null)
    setMatches([])
    setDoneMeta(null)
    setError(null)
  }, [])

  const startMatch = useCallback(async (input: { resumeText?: string; file?: File }) => {
    reset()
    setPhase('streaming')
    setStageLabel('Starting match…')

    const controller = new AbortController()
    abortRef.current = controller

    const handlers = {
      onStatus: (event: StatusEvent) => {
        setStageLabel(STAGE_LABELS[event.stage])
      },
      onMatch: (match: JobMatch) => {
        setMatches((prev) => [...prev, match])
      },
      onDone: (event: DoneEvent) => {
        setDoneMeta(event)
        setPhase('done')
        setStageLabel(null)
      },
      onError: (event: { message: string }) => {
        setError(event.message)
        setPhase('error')
        setStageLabel(null)
      },
    }

    try {
      if (input.file) {
        await streamMatchFromPdf(input.file, handlers, controller.signal)
      } else if (input.resumeText?.trim()) {
        await streamMatchFromText(input.resumeText.trim(), handlers, controller.signal)
      } else {
        setError('Paste your resume or upload a PDF first.')
        setPhase('error')
        return
      }
    } catch (err) {
      if ((err as Error).name === 'AbortError') return
      setError(err instanceof Error ? err.message : 'Match request failed')
      setPhase('error')
    }
  }, [reset])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setPhase('idle')
    setStageLabel(null)
  }, [])

  return {
    phase,
    stageLabel,
    matches,
    doneMeta,
    error,
    startMatch,
    reset,
    cancel,
  }
}
