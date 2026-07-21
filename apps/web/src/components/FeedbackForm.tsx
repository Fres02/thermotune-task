import { useState, type FormEvent } from 'react'
import { CHANGE_REASONS } from '../api/types'
import type { ChangeReason } from '../api/types'

interface Props {
  onSubmit: (reason: ChangeReason | null, comment: string) => void
  submitting: boolean
  errors: string[]
  onBack: () => void
}

export function FeedbackForm({ onSubmit, submitting, errors, onBack }: Props) {
  const [reason, setReason] = useState<ChangeReason | ''>('')
  const [comment, setComment] = useState('')

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onSubmit(reason === '' ? null : reason, comment.trim())
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2>Confirm decision</h2>

      <label>
        Reason for modification (optional)
        <select value={reason} onChange={(event) => setReason(event.target.value as ChangeReason | '')}>
          <option value="">Select a reason...</option>
          {CHANGE_REASONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <label>
        Comment (optional)
        <textarea value={comment} onChange={(event) => setComment(event.target.value)} rows={3} />
      </label>

      {errors.length > 0 && (
        <ul className="error-list">
          {errors.map((error) => (
            <li key={error}>{error}</li>
          ))}
        </ul>
      )}

      <div className="editor-actions">
        <button type="button" className="secondary" onClick={onBack}>
          Back
        </button>
        <button type="submit" disabled={submitting}>
          {submitting ? 'Submitting...' : 'Submit decision'}
        </button>
      </div>
    </form>
  )
}
