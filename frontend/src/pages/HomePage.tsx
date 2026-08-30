import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import UploadForm from '../components/UploadForm'

export default function HomePage() {
  const navigate = useNavigate()

  const handleSubmit = (pipelineId: string) => {
    navigate(`/pipeline/${pipelineId}`)
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Autonomous Paper Reproduction
        </h2>
        <p className="text-lg text-gray-600">
          Upload a research paper PDF and watch the system autonomously reproduce its implementation and verify results.
        </p>
      </div>

      <UploadForm onSubmit={handleSubmit} />

      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-3">How It Works</h3>
        <ol className="space-y-2 text-sm text-blue-800">
          <li>1. <strong>PARSE:</strong> Extract paper specification (architecture, hyperparameters, datasets)</li>
          <li>2. <strong>PLAN:</strong> Create implementation plan</li>
          <li>3. <strong>GENERATE:</strong> Generate executable code</li>
          <li>4. <strong>EXECUTE:</strong> Run code in isolated Docker sandbox</li>
          <li>5. <strong>VERIFY:</strong> Compare results with paper claims</li>
        </ol>
      </div>

      <div className="mt-6 text-center text-sm text-gray-500">
        <p>
          This system goes beyond code generation — it empirically verifies reproduction through actual execution.
        </p>
      </div>
    </div>
  )
}
