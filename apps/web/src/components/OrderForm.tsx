import { useState, type FormEvent } from 'react'
import type { OrderCreateRequest } from '../api/types'

interface Props {
  onSubmit: (payload: OrderCreateRequest) => void
  submitting: boolean
  errors: string[]
}

export function OrderForm({ onSubmit, submitting, errors }: Props) {
  const [quantity, setQuantity] = useState('2400')
  const [availableSizes, setAvailableSizes] = useState('500, 800, 1000')
  const [minSize, setMinSize] = useState('400')
  const [maxSize, setMaxSize] = useState('1000')

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const sizes = availableSizes
      .split(',')
      .map((size) => size.trim())
      .filter(Boolean)
      .map(Number)

    onSubmit({
      order_quantity_kg: Number(quantity),
      available_batch_sizes_kg: sizes,
      minimum_batch_size_kg: Number(minSize),
      maximum_batch_size_kg: Number(maxSize),
    })
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2>New order</h2>

      <label>
        Order quantity (kg)
        <input
          type="number"
          value={quantity}
          onChange={(event) => setQuantity(event.target.value)}
          required
          min="0"
          step="any"
        />
      </label>

      <label>
        Available batch sizes (kg, comma-separated)
        <input
          value={availableSizes}
          onChange={(event) => setAvailableSizes(event.target.value)}
          placeholder="500, 800, 1000"
        />
      </label>

      <div className="row">
        <label>
          Minimum batch size (kg)
          <input
            type="number"
            value={minSize}
            onChange={(event) => setMinSize(event.target.value)}
            required
            min="0"
            step="any"
          />
        </label>
        <label>
          Maximum batch size (kg)
          <input
            type="number"
            value={maxSize}
            onChange={(event) => setMaxSize(event.target.value)}
            required
            min="0"
            step="any"
          />
        </label>
      </div>

      {errors.length > 0 && (
        <ul className="error-list">
          {errors.map((error) => (
            <li key={error}>{error}</li>
          ))}
        </ul>
      )}

      <button type="submit" disabled={submitting}>
        {submitting ? 'Generating suggestions...' : 'Generate suggestions'}
      </button>
    </form>
  )
}
