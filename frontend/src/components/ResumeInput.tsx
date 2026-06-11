type ResumeInputProps = {
  resumeText: string
  onResumeTextChange: (value: string) => void
  selectedFile: File | null
  onFileChange: (file: File | null) => void
  disabled?: boolean
  onLoadSample: () => void
  loadingSample?: boolean
}

export function ResumeInput({
  resumeText,
  onResumeTextChange,
  selectedFile,
  onFileChange,
  disabled,
  onLoadSample,
  loadingSample,
}: ResumeInputProps) {
  return (
    <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-slate-900">Your resume</h2>
        <button
          type="button"
          onClick={onLoadSample}
          disabled={disabled || loadingSample}
          className="text-sm font-medium text-indigo-600 hover:text-indigo-700 disabled:opacity-50"
        >
          {loadingSample ? 'Loading sample…' : 'Load sample resume'}
        </button>
      </div>

      <textarea
        value={resumeText}
        onChange={(e) => onResumeTextChange(e.target.value)}
        disabled={disabled}
        rows={12}
        placeholder="Paste your resume here…"
        className="w-full resize-y rounded-lg border border-slate-300 px-3 py-2 text-sm leading-relaxed text-slate-800 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200 disabled:bg-slate-50"
      />

      <div className="flex flex-wrap items-center gap-3">
        <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 has-disabled:cursor-not-allowed has-disabled:opacity-50">
          <input
            type="file"
            accept="application/pdf,.pdf"
            disabled={disabled}
            className="sr-only"
            onChange={(e) => onFileChange(e.target.files?.[0] ?? null)}
          />
          Upload PDF
        </label>
        {selectedFile && (
          <span className="text-sm text-slate-600">
            Selected: <span className="font-medium">{selectedFile.name}</span>
          </span>
        )}
        <span className="text-xs text-slate-500">PDF upload overrides pasted text for matching</span>
      </div>
    </div>
  )
}
