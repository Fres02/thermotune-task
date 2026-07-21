import { useState } from 'react'
import './App.css'
import { ApiRequestError, createOrder, submitDecision } from './api/client'
import type { ChangeReason, DecisionResponse, OrderCreateRequest, OrderResponse, SuggestionOut } from './api/types'
import { BatchEditor } from './components/BatchEditor'
import { Dashboard } from './components/Dashboard'
import { FeedbackForm } from './components/FeedbackForm'
import { OrderForm } from './components/OrderForm'
import { SuggestionsList } from './components/SuggestionsList'

type View = 'new-order' | 'dashboard'
type Step = 'form' | 'suggestions' | 'editor' | 'feedback' | 'done'

function App() {
  const [view, setView] = useState<View>('new-order')
  const [step, setStep] = useState<Step>('form')

  const [orderResult, setOrderResult] = useState<OrderResponse | null>(null)
  const [orderPayload, setOrderPayload] = useState<OrderCreateRequest | null>(null)
  const [editingBatches, setEditingBatches] = useState<number[]>([])
  const [cameFromEditor, setCameFromEditor] = useState(false)
  const [decisionResult, setDecisionResult] = useState<DecisionResponse | null>(null)

  const [orderFormErrors, setOrderFormErrors] = useState<string[]>([])
  const [decisionErrors, setDecisionErrors] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)

  const resetFlow = () => {
    setStep('form')
    setOrderResult(null)
    setOrderPayload(null)
    setEditingBatches([])
    setCameFromEditor(false)
    setDecisionResult(null)
    setOrderFormErrors([])
    setDecisionErrors([])
  }

  const handleCreateOrder = async (payload: OrderCreateRequest) => {
    setSubmitting(true)
    setOrderFormErrors([])
    try {
      const result = await createOrder(payload)
      setOrderPayload(payload)
      setOrderResult(result)
      setStep('suggestions')
    } catch (err) {
      setOrderFormErrors(err instanceof ApiRequestError ? err.errors : ['Something went wrong.'])
    } finally {
      setSubmitting(false)
    }
  }

  const handleAcceptAsIs = (suggestion: SuggestionOut) => {
    setEditingBatches(suggestion.batches)
    setCameFromEditor(false)
    setStep('feedback')
  }

  const handleEdit = (suggestion: SuggestionOut) => {
    setEditingBatches(suggestion.batches)
    setStep('editor')
  }

  const handleEditorContinue = (batches: number[]) => {
    setEditingBatches(batches)
    setCameFromEditor(true)
    setStep('feedback')
  }

  const handleSubmitDecision = async (reason: ChangeReason | null, comment: string) => {
    if (!orderResult) return
    setSubmitting(true)
    setDecisionErrors([])
    try {
      const result = await submitDecision(orderResult.order_id, {
        final_batches: editingBatches,
        change_reason: reason,
        comment: comment || null,
      })
      setDecisionResult(result)
      setStep('done')
    } catch (err) {
      setDecisionErrors(err instanceof ApiRequestError ? err.errors : ['Something went wrong.'])
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>TexTune Batch Split Engine</h1>
        <nav>
          <button
            className={view === 'new-order' ? 'active' : ''}
            onClick={() => setView('new-order')}
          >
            New order
          </button>
          <button className={view === 'dashboard' ? 'active' : ''} onClick={() => setView('dashboard')}>
            Dashboard
          </button>
        </nav>
      </header>

      <main>
        {view === 'dashboard' && <Dashboard />}

        {view === 'new-order' && (
          <>
            {step === 'form' && (
              <OrderForm onSubmit={handleCreateOrder} submitting={submitting} errors={orderFormErrors} />
            )}

            {step === 'suggestions' && orderResult && (
              <SuggestionsList
                orderId={orderResult.order_id}
                suggestions={orderResult.suggestions}
                onAcceptAsIs={handleAcceptAsIs}
                onEdit={handleEdit}
              />
            )}

            {step === 'editor' && orderPayload && (
              <BatchEditor
                initialBatches={editingBatches}
                order={orderPayload}
                onContinue={handleEditorContinue}
                onBack={() => setStep('suggestions')}
              />
            )}

            {step === 'feedback' && (
              <FeedbackForm
                onSubmit={handleSubmitDecision}
                submitting={submitting}
                errors={decisionErrors}
                onBack={() => setStep(cameFromEditor ? 'editor' : 'suggestions')}
              />
            )}

            {step === 'done' && decisionResult && (
              <div className="card">
                <h2>Decision recorded for {decisionResult.order_id}</h2>
                <p>Final plan: {decisionResult.final_batches.join(' + ')} kg</p>
                <p>Accepted without changes: {decisionResult.accepted_without_changes ? 'Yes' : 'No'}</p>
                <p>Change count: {decisionResult.change_count}</p>
                <p>Change types: {decisionResult.change_types.join(', ') || 'None'}</p>
                <p>Similarity score: {decisionResult.similarity_score.toFixed(2)}%</p>
                <button onClick={resetFlow}>Start a new order</button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}

export default App
