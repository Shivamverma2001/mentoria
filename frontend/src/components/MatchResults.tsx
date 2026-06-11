import type { DoneEvent } from '../types/match'
import type { JobMatch } from '../types/match'
import { JobMatchCard } from './JobMatchCard'

type MatchResultsProps = {
  matches: JobMatch[]
  doneMeta: DoneEvent | null
}

export function MatchResults({ matches, doneMeta }: MatchResultsProps) {
  if (matches.length === 0) return null

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-slate-900">Top matches</h2>
        {doneMeta && (
          <p className="text-xs text-slate-500">
            {doneMeta.duration_ms}ms
            {doneMeta.cache_hit ? ' · cached' : ''}
          </p>
        )}
      </div>

      <div className="space-y-4">
        {matches.map((match, index) => (
          <JobMatchCard key={match.job_id} match={match} rank={index + 1} />
        ))}
      </div>

      {doneMeta && matches.length < doneMeta.total && (
        <p className="text-sm text-amber-700">Expected {doneMeta.total} matches; received {matches.length}.</p>
      )}
    </section>
  )
}
