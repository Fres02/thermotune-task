// Lightweight mirror of the backend's services/validate.py: validate_plan.
// This exists only for instant UI feedback while editing -- the server
// re-validates with the same rules before a decision is ever saved, and its
// verdict is the one that actually gates submission.

export interface OrderBounds {
  order_quantity_kg: number
  minimum_batch_size_kg: number
  maximum_batch_size_kg: number
}

const EPSILON = 1e-6

function formatNumber(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(2)
}

export function validatePlan(plan: number[], order: OrderBounds): string[] {
  const errors: string[] = []

  const total = plan.reduce((sum, batch) => sum + batch, 0)
  if (Math.abs(total - order.order_quantity_kg) > EPSILON) {
    errors.push(
      `The final batch total is ${formatNumber(total)} kg, but the order quantity is ${formatNumber(order.order_quantity_kg)} kg.`,
    )
  }

  plan.forEach((batch, index) => {
    const position = index + 1
    if (batch <= 0) {
      errors.push(`Batch ${position} is ${formatNumber(batch)} kg, which must be a positive quantity.`)
      return
    }
    if (batch < order.minimum_batch_size_kg - EPSILON) {
      errors.push(
        `Batch ${position} is ${formatNumber(batch)} kg, which is below the minimum allowed size of ${formatNumber(order.minimum_batch_size_kg)} kg.`,
      )
    }
    if (batch > order.maximum_batch_size_kg + EPSILON) {
      errors.push(
        `Batch ${position} is ${formatNumber(batch)} kg, which is above the maximum allowed size of ${formatNumber(order.maximum_batch_size_kg)} kg.`,
      )
    }
  })

  return errors
}
