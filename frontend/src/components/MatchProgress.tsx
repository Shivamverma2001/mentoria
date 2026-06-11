import type { MatchPhase } from '../hooks/useJobMatch'

type MatchProgressProps = {
  phase: MatchPhase
  stageLabel: string | null
  matchCount: number
}

export function MatchProgress({ phase, stageLabel, matchCount }: MatchProgressProps) {
  if (phase !== 'streaming') return null

  return (
    <div className="rounded-xl border border-indigo-100 bg-indigo-50 p-4">
      <div className="flex items-center gap-3">
        <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
        <div>
          <p className="text-sm font-medium text-indigo-900">{stageLabel ?? 'Matching…'}</p>
          <p className="text-xs text-indigo-700">
            {matchCount > 0
              ? `${matchCount} of 5 matches received`
              : 'Results will appear as they are ready'}
          </p>
        </div>
      </div>
    </div>
  )
}
