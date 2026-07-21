import { useEffect, useState } from 'react'
import { getAnalyticsPreferences, getAnalyticsSummary } from '../api/client'
import type { AnalyticsSummaryResponse, PreferencesResponse } from '../api/types'

export function Dashboard() {
  const [summary, setSummary] = useState<AnalyticsSummaryResponse | null>(null)
  const [preferences, setPreferences] = useState<PreferencesResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([getAnalyticsSummary(), getAnalyticsPreferences()])
      .then(([summaryResult, preferencesResult]) => {
        setSummary(summaryResult)
        setPreferences(preferencesResult)
      })
      .catch(() => setError('Could not load analytics.'))
  }, [])

  if (error) return <div className="card">{error}</div>
  if (!summary || !preferences) return <div className="card">Loading dashboard...</div>

  const acceptanceRates = Object.entries(preferences.batch_acceptance_rates)
  const patterns = Object.entries(preferences.similar_order_patterns)

  return (
    <div className="card">
      <h2>Quality dashboard</h2>
      <div className="stat-grid">
        <div className="stat">
          <span className="stat-value">{summary.total_completed_orders}</span>
          <span className="stat-label">Completed orders</span>
        </div>
        <div className="stat">
          <span className="stat-value">{summary.acceptance_rate.toFixed(1)}%</span>
          <span className="stat-label">Acceptance rate</span>
        </div>
        <div className="stat">
          <span className="stat-value">{summary.average_changes.toFixed(2)}</span>
          <span className="stat-label">Avg. changes / order</span>
        </div>
        <div className="stat">
          <span className="stat-value">{summary.most_selected_batch_size ?? '-'}</span>
          <span className="stat-label">Most selected batch size (kg)</span>
        </div>
        <div className="stat">
          <span className="stat-value">{summary.most_common_change_reason ?? '-'}</span>
          <span className="stat-label">Most common change reason</span>
        </div>
        <div className="stat">
          <span className="stat-value">{summary.average_similarity_score.toFixed(1)}%</span>
          <span className="stat-label">Avg. similarity score</span>
        </div>
      </div>

      <h3>Historical preferences</h3>
      <div className="pref-columns">
        <div className="pref-section">
          <h4>Batch size acceptance rate</h4>
          {acceptanceRates.length === 0 ? (
            <p className="muted">No decisions recorded yet.</p>
          ) : (
            <ul>
              {acceptanceRates.map(([size, rate]) => (
                <li key={size}>
                  {size} kg &mdash; {(rate * 100).toFixed(1)}%
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="pref-section">
          <h4>Commonly chosen plans</h4>
          {patterns.length === 0 ? (
            <p className="muted">No decisions recorded yet.</p>
          ) : (
            <ul>
              {patterns.map(([plan, weight]) => (
                <li key={plan}>
                  {plan} kg &mdash; chosen {weight.toFixed(1)}x
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
