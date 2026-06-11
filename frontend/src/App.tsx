function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-4xl px-6 py-5">
          <p className="text-sm font-medium text-indigo-600">Mentoria / Arya</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">Smart Job Matcher</h1>
          <p className="mt-2 text-sm text-slate-600">
            Upload or paste a resume to find your top 5 job matches.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-8">
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-slate-500">
          Matching UI will be wired in Phase 8. Backend health:{' '}
          <code className="rounded bg-slate-100 px-2 py-1 text-sm">/api/health</code>
        </div>
      </main>
    </div>
  )
}

export default App
