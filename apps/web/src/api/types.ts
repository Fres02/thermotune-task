export interface OrderCreateRequest {
  // Omit to have the server assign the next sequential id (ORD-001, ORD-002, ...).
  order_id?: string
  order_quantity_kg: number
  available_batch_sizes_kg: number[]
  minimum_batch_size_kg: number
  maximum_batch_size_kg: number
}

export interface SuggestionOut {
  rank: number
  batches: number[]
  score: number
  recommended: boolean
  historically_preferred: boolean
  explanation: string
  explanation_polished: string | null
}

export interface OrderResponse {
  order_id: string
  suggestions: SuggestionOut[]
}

export interface DecisionResponse {
  order_id: string
  final_batches: number[]
  accepted_without_changes: boolean
  change_count: number
  change_types: string[]
  change_reason: string | null
  similarity_score: number
  created_at: string
}

export interface OrderDetailResponse {
  order_id: string
  order_quantity_kg: number
  status: string
  suggestions: SuggestionOut[]
  decision: DecisionResponse | null
}

export const CHANGE_REASONS = [
  'Better machine capacity',
  'Avoid a small batch',
  'Prefer equal batch sizes',
  'Quality requirement',
  'Delivery urgency',
  'Other',
] as const

export type ChangeReason = (typeof CHANGE_REASONS)[number]

export interface DecisionRequest {
  final_batches: number[]
  change_reason?: ChangeReason | null
  comment?: string | null
}

export interface AnalyticsSummaryResponse {
  total_completed_orders: number
  acceptance_rate: number
  average_changes: number
  most_selected_batch_size: number | null
  most_common_change_reason: string | null
  average_similarity_score: number
}

export interface PreferencesResponse {
  batch_acceptance_rates: Record<string, number>
  similar_order_patterns: Record<string, number>
}
