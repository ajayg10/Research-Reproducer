# Architecture Documentation

## System Overview

The Autonomous Research Reproducibility Engine is a multi-agent system that autonomously reproduces research papers from specification to empirical verification.

## High-Level Architecture

```
┌─────────────┐
│   Frontend  │  React + TypeScript
│  Dashboard  │  (Live Updates via WebSocket)
└──────┬──────┘
       │
       │ REST API
       │
┌──────▼──────────────────────────────────────┐
│           FastAPI Backend                    │
│  ┌────────────────────────────────────────┐ │
│  │     Orchestration Layer                │ │
│  │  (Pipeline State Machine + Retry Logic)│ │
│  └──────┬─────────────────────────────────┘ │
│         │                                    │
│    ┌────▼────┐  ┌──────┐  ┌──────┐         │
│    │ Agent 1 │  │Agent2│  │Agent3│ ...     │
│    │ Parser  │  │Planner  │Codegen│         │
│    └─────────┘  └──────┘  └──────┘         │
└──────┬──────────────────────────────────────┘
       │
       │ Gemini API
       ▼
┌─────────────────┐
│  Google Gemini  │
│   (LLM Calls)   │
└─────────────────┘

       │
       │ Docker API
       ▼
┌─────────────────┐
│  Docker Sandbox │
│  (Isolated      │
│   Execution)    │
└─────────────────┘
```

## Multi-Agent Pipeline

The system consists of 5 autonomous agents that execute sequentially:

### Agent 1: Parser
- **Input**: PDF file path or arXiv URL
- **Process**: 
  - Extract text from PDF
  - Call Gemini to extract structured specification
  - Validate against PaperSpecification schema
- **Output**: Structured paper specification (JSON)
- **Key Fields**: Architecture, hyperparameters, dataset, metrics, ambiguities

### Agent 2: Planner
- **Input**: PaperSpecification
- **Process**:
  - Analyze paper requirements
  - Create implementation plan
  - Identify what's specified vs. inferred
  - Document assumptions
- **Output**: ImplementationPlan (JSON)
- **Key Fields**: Project structure, dependencies, model/dataset/training plans

### Agent 3: Codegen
- **Input**: ImplementationPlan
- **Process**:
  - Generate Python files (model.py, dataset.py, train.py, etc.)
  - Generate requirements.txt
  - Generate configuration
  - Write all files to workspace
- **Output**: GeneratedImplementation + workspace path
- **Key Files**: 7-8 Python files + requirements + README

### Agent 4: Executor
- **Input**: Workspace path + entry point
- **Process**:
  - Create isolated Docker container
  - Mount workspace as volume
  - Install dependencies
  - Execute training script
  - Capture stdout/stderr/metrics
  - Enforce resource limits and timeout
- **Output**: ExecutionResult (status, logs, metrics, artifacts)
- **Isolation**: Non-root user, no network, CPU/memory limits

### Agent 5: Verifier
- **Input**: PaperSpecification + ExecutionResult
- **Process**:
  - Compare claimed metrics vs. reproduced metrics
  - Calculate absolute and relative differences
  - Apply tolerance thresholds
  - Categorize discrepancies
  - Determine overall verdict
- **Output**: VerificationReport (verdict, comparisons, discrepancies, score)

## Pipeline State Machine

```
QUEUED → PARSING → PLANNING → GENERATING → EXECUTING → VERIFYING → COMPLETED/PARTIAL/FAILED
                                                  ↓
                                              RETRYING (up to 3x)
                                                  ↓
                                              EXECUTING
```

## Retry Logic

The system implements intelligent retry with:
- Maximum 3 attempts per pipeline
- Retry decision based on error type:
  - ✅ Retry: Timeout, network errors, dependency failures
  - ❌ Don't retry: Syntax errors, import errors, deterministic bugs
- Retry history tracked for debugging
- Correction prompts generated for LLM-based fixes (future enhancement)

## Data Flow

1. **User uploads PDF** → Frontend → Backend API
2. **API starts pipeline** → Creates PipelineState → Storage
3. **Parser agent** → Gemini API → PaperSpecification → Storage
4. **Planner agent** → Gemini API → ImplementationPlan → Storage
5. **Codegen agent** → Gemini API → Generated files → Filesystem
6. **Executor agent** → Docker API → Sandbox execution → Metrics → Storage
7. **Verifier agent** → Metric comparison → Report → Storage
8. **Frontend polls/WebSocket** → Live updates → User

## Storage Architecture

### Local Mode (MVP)
- SQLite for pipeline state
- Filesystem for generated code, artifacts, logs
- Directory structure:
  ```
  storage/
    pipelines/          # Pipeline state JSON files
    artifacts/          # Execution logs, plots
    uploads/            # Uploaded PDFs
  generated/            # Generated code workspaces
  sandbox/              # Sandbox execution artifacts
  ```

### Cloud Mode (Deployment)
- Firestore for pipeline state
- Cloud Storage for artifacts
- Same abstraction layer via StorageService

## Security Model

### Sandbox Isolation
- Docker containers with:
  - Non-root execution (user: nobody)
  - No network access (network_mode: none)
  - CPU quota (configurable)
  - Memory limits (default: 4GB)
  - Timeout (default: 10 minutes)
  - Ephemeral filesystem
  - No access to:
    - Host filesystem (except mounted workspace)
    - Docker socket
    - Credentials or secrets

### Untrusted Code Handling
- All LLM-generated code treated as untrusted
- Never executed on host system
- Sandbox process killed on timeout
- No privileged operations allowed

## API Endpoints

### REST API
- `POST /api/reproduce` - Start reproduction with paper path
- `POST /api/reproduce/upload` - Upload PDF and start
- `GET /api/pipeline/{id}` - Get pipeline status
- `GET /api/pipeline/{id}/full` - Get complete state
- `GET /api/pipelines` - List recent pipelines
- `GET /api/pipeline/{id}/report` - Get verification report
- `GET /api/pipeline/{id}/code` - Get generated code

### WebSocket
- `WS /ws/pipeline/{id}` - Subscribe to live pipeline updates
- Messages: `initial_state`, `state_update`, `pipeline_complete`

## Technology Stack

### Backend
- **Framework**: FastAPI (async Python web framework)
- **LLM**: Google Gemini via `google-generativeai` SDK
- **Agents**: Custom BaseAgent class + 5 specialized agents
- **Validation**: Pydantic models for structured I/O
- **Storage**: SQLite (local) / Firestore (cloud)
- **Sandbox**: Docker Python SDK
- **Logging**: structlog (structured JSON logs)

### Frontend
- **Framework**: React 18 + TypeScript
- **Build**: Vite
- **Styling**: TailwindCSS
- **HTTP**: Axios
- **State**: React Query
- **Routing**: React Router
- **WebSocket**: Native WebSocket API

### Infrastructure
- **Orchestration**: Google ADK (planned integration)
- **Cloud**: Google Cloud Run (API), GKE (heavy jobs)
- **Database**: Firestore
- **Storage**: Cloud Storage
- **Monitoring**: Cloud Logging

## Scalability Considerations

### Current (MVP)
- Single-threaded pipeline execution
- Local storage
- CPU-only sandbox
- 10-minute timeout

### Future Enhancements
- Parallel pipeline execution
- GPU support for heavy models
- GKE Jobs for long-running execution
- Distributed tracing
- Rate limiting
- Caching layer for common papers

## Error Handling

- All agents return structured success/failure
- Errors captured at each stage
- Pipeline state persisted on every transition
- WebSocket broadcasts failures in real-time
- Retry logic with bounded attempts
- Detailed error messages for debugging

## Observability

- Structured logging at every stage
- Token usage tracking (Gemini calls)
- Execution time per agent
- Resource usage in sandbox
- Pipeline state history
- Retry history

## Deployment Architecture

```
┌─────────────────────────────────────────────┐
│             Google Cloud Run                │
│  ┌─────────────────────────────────────┐   │
│  │   FastAPI Backend Container         │   │
│  │   (Orchestration + Agents)          │   │
│  └──────────┬──────────────────────────┘   │
└─────────────┼──────────────────────────────┘
              │
       ┌──────┴───────┬────────────┬─────────┐
       │              │            │         │
   ┌───▼───┐    ┌────▼────┐  ┌───▼────┐  ┌─▼──────┐
   │Vertex │    │Firestore│  │Cloud   │  │  GKE   │
   │  AI   │    │ (State) │  │Storage │  │(Sandbox│
   │(Gemini│    │         │  │(Files) │  │ Jobs)  │
   └───────┘    └─────────┘  └────────┘  └────────┘
```

## Key Design Decisions

1. **Structured Output**: All agent I/O validated via Pydantic schemas
2. **Stateful Pipeline**: Full state persisted at every stage
3. **Fail-Fast**: Agents return early on failure rather than continuing
4. **Retry with Context**: Retry decisions based on error analysis
5. **Security-First**: All generated code runs in isolated sandbox
6. **Observable**: Comprehensive logging and state tracking
7. **Extensible**: BaseAgent pattern allows easy agent addition
8. **Cloud-Ready**: Storage abstraction supports local/cloud modes
