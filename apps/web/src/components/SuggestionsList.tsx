import type { SuggestionOut } from '../api/types'

const MAX_DISPLAYED = 8

interface Props {
  orderId: string
  suggestions: SuggestionOut[]
  onAcceptAsIs: (suggestion: SuggestionOut) => void
  onEdit: (suggestion: SuggestionOut) => void
}

export function SuggestionsList({ orderId, suggestions, onAcceptAsIs, onEdit }: Props) {
  const displayed = suggestions.slice(0, MAX_DISPLAYED)
  const hiddenCount = suggestions.length - displayed.length

  return (
    <div className="card">
      <h2>Suggested plans for {orderId}</h2>
      <div className="suggestions">
        {displayed.map((suggestion) => (
          <div key={suggestion.rank} className={`suggestion${suggestion.recommended ? ' recommended' : ''}`}>
            <div className="suggestion-header">
              <span className="rank">Rank {suggestion.rank}</span>
              {suggestion.recommended && <span className="badge">Recommended</span>}
              {suggestion.historically_preferred && (
                <span className="badge badge-outline">Previously user preferred</span>
              )}
              <span className="score">Score {suggestion.score.toFixed(1)}</span>
            </div>
            <div className="batches">{suggestion.batches.map((batch) => `${batch} kg`).join(' + ')}</div>
            <p className="explanation">{suggestion.explanation_polished ?? suggestion.explanation}</p>
            <div className="actions">
              <button onClick={() => onAcceptAsIs(suggestion)}>Accept</button>
              <button className="secondary" onClick={() => onEdit(suggestion)}>
                Select &amp; edit
              </button>
            </div>
          </div>
        ))}
      </div>
      {hiddenCount > 0 && <p className="muted">{hiddenCount} more valid plan(s) not shown.</p>}
    </div>
  )
}
