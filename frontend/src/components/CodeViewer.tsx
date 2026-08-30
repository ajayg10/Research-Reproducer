import { useState } from 'react'

interface CodeViewerProps {
  implementation: any
}

export default function CodeViewer({ implementation }: CodeViewerProps) {
  const [selectedFile, setSelectedFile] = useState<string | null>(null)

  if (!implementation || !implementation.files) {
    return null
  }

  const files = implementation.files
  const currentFile = selectedFile
    ? files.find((f: any) => f.path === selectedFile)
    : files[0]

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Generated Code
      </h2>

      <div className="flex space-x-4 mb-4">
        {files.map((file: any) => (
          <button
            key={file.path}
            onClick={() => setSelectedFile(file.path)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              (selectedFile === file.path || (!selectedFile && file === files[0]))
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {file.path}
          </button>
        ))}
      </div>

      {currentFile && (
        <div>
          <div className="mb-2 text-sm text-gray-600">
            {currentFile.purpose}
          </div>
          <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
            <pre className="text-sm text-gray-100 font-mono">
              <code>{currentFile.content}</code>
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
