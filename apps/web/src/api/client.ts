import type {
  AnalyticsSummaryResponse,
  DecisionRequest,
  DecisionResponse,
  OrderCreateRequest,
  OrderDetailResponse,
  OrderResponse,
  PreferencesResponse,
} from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiRequestError extends Error {
  errors: string[]

  constructor(errors: string[]) {
    super(errors.join(' '))
    this.errors = errors
  }
}

function extractErrors(detail: unknown): string[] {
  if (Array.isArray(detail)) {
    return detail.map((item) =>
      typeof item === 'string' ? item : ((item as { msg?: string }).msg ?? JSON.stringify(item)),
    )
  }
  if (typeof detail === 'string') return [detail]
  return ['Something went wrong.']
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: [`Request failed with status ${res.status}`] }))
    throw new ApiRequestError(extractErrors(body.detail))
  }

  return res.json() as Promise<T>
}

export async function checkHealth(): Promise<void> {
  await request('/api/health')
}

export function createOrder(payload: OrderCreateRequest): Promise<OrderResponse> {
  return request('/api/orders', { method: 'POST', body: JSON.stringify(payload) })
}

export function getOrder(orderId: string): Promise<OrderDetailResponse> {
  return request(`/api/orders/${encodeURIComponent(orderId)}`)
}

export function submitDecision(orderId: string, payload: DecisionRequest): Promise<DecisionResponse> {
  return request(`/api/orders/${encodeURIComponent(orderId)}/decision`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getAnalyticsSummary(): Promise<AnalyticsSummaryResponse> {
  return request('/api/analytics/summary')
}

export function getAnalyticsPreferences(): Promise<PreferencesResponse> {
  return request('/api/analytics/preferences')
}
