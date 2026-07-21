import { useMemo, useState } from 'react'
import type { OrderBounds } from '../utils/validate'
import { validatePlan } from '../utils/validate'

interface Props {
  initialBatches: number[]
  order: OrderBounds
  onContinue: (batches: number[]) => void
  onBack: () => void
}

export function BatchEditor({ initialBatches, order, onContinue, onBack }: Props) {
  const [batches, setBatches] = useState<number[]>(initialBatches)
  const [selectedForMerge, setSelectedForMerge] = useState<number[]>([])

  const total = useMemo(() => batches.reduce((sum, batch) => sum + batch, 0), [batches])
  const remaining = order.order_quantity_kg - total
  const errors = useMemo(() => validatePlan(batches, order), [batches, order])
  const isValid = errors.length === 0

  const updateBatch = (index: number, value: number) => {
    setBatches((prev) => prev.map((batch, i) => (i === index ? value : batch)))
  }

  const removeBatch = (index: number) => {
    setBatches((prev) => prev.filter((_, i) => i !== index))
    setSelectedForMerge((prev) => prev.filter((i) => i !== index).map((i) => (i > index ? i - 1 : i)))
  }

  const splitBatch = (index: number) => {
    setBatches((prev) => {
      const value = prev[index]
      const half1 = Math.floor(value / 2)
      const half2 = value - half1
      const next = [...prev]
      next.splice(index, 1, half1, half2)
      return next
    })
    setSelectedForMerge([])
  }

  const addBatch = () => {
    setBatches((prev) => [...prev, order.minimum_batch_size_kg])
  }

  const toggleMergeSelection = (index: number) => {
    setSelectedForMerge((prev) => {
      if (prev.includes(index)) return prev.filter((i) => i !== index)
      if (prev.length >= 2) return prev
      return [...prev, index]
    })
  }

  const mergeSelected = () => {
    if (selectedForMerge.length !== 2) return
    const [a, b] = [...selectedForMerge].sort((x, y) => x - y)
    setBatches((prev) => {
      const merged = prev[a] + prev[b]
      const next = prev.filter((_, i) => i !== a && i !== b)
      next.splice(a, 0, merged)
      return next
    })
    setSelectedForMerge([])
  }

  return (
    <div className="card">
      <h2>Edit batch plan</h2>

      <div className={`total-banner ${isValid ? 'valid' : 'invalid'}`}>
        Total: {total} kg / {order.order_quantity_kg} kg
        {Math.abs(remaining) > 1e-6 &&
          (remaining > 0 ? ` (${remaining} kg remaining)` : ` (${Math.abs(remaining)} kg over)`)}
      </div>

      <table className="batch-table">
        <thead>
          <tr>
            <th>Batch</th>
            <th>Quantity (kg)</th>
            <th>Merge</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {batches.map((batch, index) => (
            <tr key={index}>
              <td>{index + 1}</td>
              <td>
                <input
                  type="number"
                  value={batch}
                  onChange={(event) => updateBatch(index, Number(event.target.value))}
                  step="any"
                />
              </td>
              <td>
                <input
                  type="checkbox"
                  checked={selectedForMerge.includes(index)}
                  onChange={() => toggleMergeSelection(index)}
                  aria-label={`Select batch ${index + 1} for merge`}
                />
              </td>
              <td className="row-actions">
                <button type="button" onClick={() => splitBatch(index)}>
                  Split
                </button>
                <button type="button" onClick={() => removeBatch(index)} disabled={batches.length <= 1}>
                  Remove
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="editor-actions">
        <button type="button" onClick={addBatch}>
          Add batch
        </button>
        <button type="button" onClick={mergeSelected} disabled={selectedForMerge.length !== 2}>
          Merge selected
        </button>
      </div>

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
        <button type="button" disabled={!isValid} onClick={() => onContinue(batches)}>
          Continue
        </button>
      </div>
    </div>
  )
}
