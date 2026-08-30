interface MetricsTableProps {
  report: any
}

export default function MetricsTable({ report }: MetricsTableProps) {
  if (!report || !report.report) {
    return null
  }

  const { metric_comparisons, verdict, reproduction_quality_score, summary } = report.report

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Verification Report
      </h2>

      <div className={`mb-6 p-4 rounded-lg ${
        verdict === 'successful' ? 'bg-green-50 border border-green-200' :
        verdict === 'partial' ? 'bg-yellow-50 border border-yellow-200' :
        'bg-red-50 border border-red-200'
      }`}>
        <p className="font-semibold text-lg">
          Status: <span className="uppercase">{verdict}</span>
        </p>
        {reproduction_quality_score !== null && (
          <p className="text-sm mt-1">
            Quality Score: {(reproduction_quality_score * 100).toFixed(1)}%
          </p>
        )}
      </div>

      {metric_comparisons && metric_comparisons.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Metric
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Paper
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Reproduced
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Difference
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {metric_comparisons.map((metric: any, index: number) => (
                <tr key={index}>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">
                    {metric.metric_name}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {metric.claimed_value?.toFixed(4) || 'N/A'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {metric.reproduced_value?.toFixed(4) || 'N/A'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {metric.relative_difference !== null
                      ? `${(metric.relative_difference * 100).toFixed(2)}%`
                      : 'N/A'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`status-badge ${
                      metric.status === 'PASS' ? 'status-completed' :
                      metric.status === 'FAIL' ? 'status-failed' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {metric.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {summary && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-semibold text-gray-900 mb-2">Summary</h3>
          <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
            {summary}
          </pre>
        </div>
      )}
    </div>
  )
}
