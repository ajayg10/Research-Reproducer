import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import PipelineView from '../components/PipelineView'
import CodeViewer from '../components/CodeViewer'
import MetricsTable from '../components/MetricsTable'

const WS_URL = 'ws://localhost:8000'

export default function PipelinePage() {
  const { pipelineId } = useParams<{ pipelineId: string }>()
  const [state, setState] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!pipelineId) return

    // Fetch initial state
    fetch(`http://localhost:8000/api/pipeline/${pipelineId}/full`)
      .then((res) => res.json())
      .then((data) => {
        setState(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })

    // Connect to WebSocket for live updates
    const ws = new WebSocket(`${WS_URL}/ws/pipeline/${pipelineId}`)

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)

      if (message.type === 'state_update' || message.type === 'initial_state') {
        // Refresh full state
        fetch(`http://localhost:8000/api/pipeline/${pipelineId}/full`)
          .then((res) => res.json())
          .then((data) => setState(data))
      }
    }

    ws.onerror = (err) => {
      console.error('WebSocket error:', err)
    }

    return () => {
      ws.close()
    }
  }, [pipelineId])

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <p className="mt-4 text-gray-600">Loading pipeline...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <p className="text-red-800">Error: {error}</p>
      </div>
    )
  }

  if (!state) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Pipeline not found</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Pipeline: {pipelineId}
        </h1>
        <p className="text-sm text-gray-600">
          Source: {state.paper_source}
        </p>
        <p className="text-sm text-gray-600">
          Started: {new Date(state.created_at).toLocaleString()}
        </p>
      </div>

      <PipelineView
        currentStatus={state.status}
        retryCount={state.retry_count}
        error={state.error}
      />

      {state.codegen_output?.implementation && (
        <CodeViewer implementation={state.codegen_output.implementation} />
      )}

      {state.verifier_output && (
        <MetricsTable report={state.verifier_output} />
      )}

      {state.executor_output?.result?.stdout && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Execution Logs
          </h2>
          <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
            <pre className="text-sm text-gray-100 font-mono">
              {state.executor_output.result.stdout}
            </pre>
          </div>
          {state.executor_output.result.stderr && (
            <div className="mt-4">
              <h3 className="font-semibold text-red-700 mb-2">Errors:</h3>
              <div className="bg-red-50 rounded-lg p-4 overflow-x-auto">
                <pre className="text-sm text-red-800 font-mono">
                  {state.executor_output.result.stderr}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
