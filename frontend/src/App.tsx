import { useState } from 'react'
import { MatchProgress } from './components/MatchProgress'
import { MatchResults } from './components/MatchResults'
import { ResumeInput } from './components/ResumeInput'
import { useJobMatch } from './hooks/useJobMatch'

function App() {
  const [resumeText, setResumeText] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [loadingSample, setLoadingSample] = useState(false)

  const { phase, stageLabel, matches, doneMeta, error, startMatch, reset, cancel } =
    useJobMatch()

  const isStreaming = phase === 'streaming'

  async function handleLoadSample() {
    setLoadingSample(true)
    try {
      const response = await fetch('/sample_resume_aarav_mehta.txt')
      if (!response.ok) throw new Error('Could not load sample resume')
      setResumeText(await response.text())
      setSelectedFile(null)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to load sample')
    } finally {
      setLoadingSample(false)
    }
  }

  function handleMatch() {
    void startMatch({
      resumeText: selectedFile ? undefined : resumeText,
      file: selectedFile ?? undefined,
    })
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-4xl px-6 py-5">
          <p className="text-sm font-medium text-indigo-600">Mentoria / Arya</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">Smart Job Matcher</h1>
          <p className="mt-2 text-sm text-slate-600">
            Paste or upload your resume to stream your top 5 job matches with personalized reasoning.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-4xl space-y-6 px-6 py-8">
        <ResumeInput
          resumeText={resumeText}
          onResumeTextChange={setResumeText}
          selectedFile={selectedFile}
          onFileChange={setSelectedFile}
          disabled={isStreaming}
          onLoadSample={() => void handleLoadSample()}
          loadingSample={loadingSample}
        />

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleMatch}
            disabled={isStreaming || (!resumeText.trim() && !selectedFile)}
            className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-indigo-300"
          >
            {isStreaming ? 'Matching…' : 'Match jobs'}
          </button>
          {isStreaming && (
            <button
              type="button"
              onClick={cancel}
              className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
          )}
          {(phase === 'done' || phase === 'error') && (
            <button
              type="button"
              onClick={reset}
              className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Clear results
            </button>
          )}
        </div>

        <MatchProgress phase={phase} stageLabel={stageLabel} matchCount={matches.length} />

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            {error}
          </div>
        )}

        <MatchResults matches={matches} doneMeta={doneMeta} />
      </main>
    </div>
  )
}

export default App
