interface PipelineStage {
  name: string
  status: 'pending' | 'active' | 'completed' | 'failed'
}

interface PipelineViewProps {
  currentStatus: string
  retryCount: number
  error?: string
}

export default function PipelineView({ currentStatus, retryCount, error }: PipelineViewProps) {
  const stages: PipelineStage[] = [
    {
      name: 'PARSING',
      status: getStageStatus('parsing', currentStatus),
    },
    {
      name: 'PLANNING',
      status: getStageStatus('planning', currentStatus),
    },
    {
      name: 'GENERATING',
      status: getStageStatus('generating', currentStatus),
    },
    {
      name: 'EXECUTING',
      status: getStageStatus('executing', currentStatus),
    },
    {
      name: 'VERIFYING',
      status: getStageStatus('verifying', currentStatus),
    },
  ]

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">
        Pipeline Progress
      </h2>

      <div className="space-y-4">
        {stages.map((stage, index) => (
          <div key={stage.name} className="flex items-center">
            <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center border-2
              ${stage.status === 'completed' ? 'bg-green-500 border-green-500 text-white' : ''}
              ${stage.status === 'active' ? 'bg-blue-500 border-blue-500 text-white animate-pulse' : ''}
              ${stage.status === 'failed' ? 'bg-red-500 border-red-500 text-white' : ''}
              ${stage.status === 'pending' ? 'bg-white border-gray-300 text-gray-400' : ''}
            ">
              {stage.status === 'completed' ? '✓' : index + 1}
            </div>

            <div className="ml-4 flex-1">
              <p className={`font-medium ${
                stage.status === 'active' ? 'text-blue-700' :
                stage.status === 'completed' ? 'text-green-700' :
                stage.status === 'failed' ? 'text-red-700' :
                'text-gray-500'
              }`}>
                {stage.name}
              </p>
              {stage.status === 'active' && (
                <p className="text-sm text-gray-600">In progress...</p>
              )}
            </div>
          </div>
        ))}
      </div>

      {retryCount > 0 && (
        <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-800">
            <strong>Retry Attempt:</strong> {retryCount} / 3
          </p>
        </div>
      )}

      {error && (
        <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">
            <strong>Error:</strong> {error}
          </p>
        </div>
      )}

      {(currentStatus === 'completed' || currentStatus === 'partial' || currentStatus === 'failed') && (
        <div className={`mt-6 rounded-lg p-4 ${
          currentStatus === 'completed' ? 'bg-green-50 border border-green-200' :
          currentStatus === 'partial' ? 'bg-yellow-50 border border-yellow-200' :
          'bg-red-50 border border-red-200'
        }`}>
          <p className={`font-semibold ${
            currentStatus === 'completed' ? 'text-green-800' :
            currentStatus === 'partial' ? 'text-yellow-800' :
            'text-red-800'
          }`}>
            Pipeline {currentStatus === 'completed' ? 'Completed Successfully' :
                     currentStatus === 'partial' ? 'Completed Partially' :
                     'Failed'}
          </p>
        </div>
      )}
    </div>
  )
}

function getStageStatus(stageName: string, currentStatus: string): PipelineStage['status'] {
  const stages = ['parsing', 'planning', 'generating', 'executing', 'verifying']
  const currentIndex = stages.indexOf(currentStatus.toLowerCase())
  const stageIndex = stages.indexOf(stageName.toLowerCase())

  if (currentStatus === 'failed') {
    if (stageIndex < currentIndex) return 'completed'
    if (stageIndex === currentIndex) return 'failed'
    return 'pending'
  }

  if (stageIndex < currentIndex) return 'completed'
  if (stageIndex === currentIndex) return 'active'
  return 'pending'
}
