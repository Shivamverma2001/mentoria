import type { JobMatch } from '../types/match'

type JobMatchCardProps = {
  match: JobMatch
  rank: number
}

function scoreColor(score: number): string {
  if (score >= 85) return 'bg-emerald-100 text-emerald-800'
  if (score >= 70) return 'bg-amber-100 text-amber-800'
  return 'bg-slate-100 text-slate-700'
}

export function JobMatchCard({ match, rank }: JobMatchCardProps) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            #{rank} match
          </p>
          <h3 className="mt-1 text-lg font-semibold text-slate-900">{match.title}</h3>
          <p className="text-sm font-medium text-slate-700">{match.company}</p>
          <p className="mt-1 text-xs text-slate-500">
            {match.location} · {match.remote}
          </p>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-sm font-semibold ${scoreColor(match.match_score)}`}
        >
          {match.match_score}/100
        </span>
      </div>

      <p className="mt-4 text-sm leading-relaxed text-slate-700">{match.reasoning}</p>

      <div className="mt-4 rounded-lg border border-slate-100 bg-slate-50 p-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Highlight in cover letter
        </p>
        <p className="mt-1 text-sm italic text-slate-800">"{match.highlight_bullet}"</p>
      </div>
    </article>
  )
}
