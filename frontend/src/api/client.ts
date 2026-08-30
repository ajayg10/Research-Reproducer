import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export interface ReproductionRequest {
  paper_source: string
  paper_title?: string
}

export interface ReproductionResponse {
  pipeline_id: string
  status: string
  message: string
}

export interface PipelineStatus {
  pipeline_id: string
  status: string
  current_stage: string
  retry_count: number
  created_at: string
  updated_at: string
  error?: string
}

export interface PipelineState {
  pipeline_id: string
  status: string
  paper_source: string
  created_at: string
  updated_at: string
  parser_output?: any
  planner_output?: any
  codegen_output?: any
  executor_output?: any
  verifier_output?: any
  retry_count: number
  retry_history: any[]
  error?: string
}

export const api = {
  // Start reproduction with PDF path or arXiv URL
  async startReproduction(request: ReproductionRequest): Promise<ReproductionResponse> {
    const response = await axios.post(`${API_BASE_URL}/reproduce`, request)
    return response.data
  },

  // Upload PDF and start reproduction
  async uploadAndReproduce(file: File): Promise<ReproductionResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post(`${API_BASE_URL}/reproduce/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // Get pipeline status
  async getPipelineStatus(pipelineId: string): Promise<PipelineStatus> {
    const response = await axios.get(`${API_BASE_URL}/pipeline/${pipelineId}`)
    return response.data
  },

  // Get full pipeline state
  async getPipelineFull(pipelineId: string): Promise<PipelineState> {
    const response = await axios.get(`${API_BASE_URL}/pipeline/${pipelineId}/full`)
    return response.data
  },

  // List recent pipelines
  async listPipelines(limit = 10): Promise<PipelineStatus[]> {
    const response = await axios.get(`${API_BASE_URL}/pipelines?limit=${limit}`)
    return response.data
  },

  // Get verification report
  async getVerificationReport(pipelineId: string): Promise<any> {
    const response = await axios.get(`${API_BASE_URL}/pipeline/${pipelineId}/report`)
    return response.data
  },

  // Get generated code
  async getGeneratedCode(pipelineId: string): Promise<any> {
    const response = await axios.get(`${API_BASE_URL}/pipeline/${pipelineId}/code`)
    return response.data
  },
}

export default api
