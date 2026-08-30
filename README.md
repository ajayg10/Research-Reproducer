# Autonomous Research Reproducibility Engine

An agentic system that autonomously reproduces computer science and ML research papers from PDF to verified results.

## Overview

This system takes a research paper (PDF or arXiv URL) and:
1. **Parses** the paper to extract specifications
2. **Plans** an implementation strategy
3. **Generates** executable code
4. **Executes** the implementation in a secure sandbox
5. **Verifies** results against the paper's claimed metrics
6. **Retries** on failure with corrections
7. **Reports** reproducibility status and discrepancies

**Key Differentiator:** This is NOT a chatbot that explains papers. It autonomously executes and empirically verifies the implementation.

## Architecture

### Multi-Agent System

- **Agent 1 (Parser)**: Extracts structured specifications from PDFs
- **Agent 2 (Planner)**: Creates implementation plans
- **Agent 3 (Codegen)**: Generates executable code
- **Agent 4 (Executor)**: Runs code in isolated Docker sandbox
- **Agent 5 (Verifier)**: Compares results with paper claims

### Technology Stack

- **Backend**: Python 3.11+, FastAPI, Google ADK
- **LLM**: Google Gemini (via Vertex AI)
- **Frontend**: React, TypeScript, Vite, TailwindCSS
- **Sandbox**: Docker with resource limits
- **Storage**: SQLite (local) / Firestore (cloud)
- **Cloud**: Google Cloud Run, GKE, Cloud Storage

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker
- Google Cloud account with Gemini API access

### Local Development Setup

1. **Clone and setup environment**:
```bash
git clone <repo-url>
cd Researchreproducability
cp .env.example .env
# Edit .env with your Gemini API key
```

2. **Backend setup**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Frontend setup**:
```bash
cd frontend
npm install
```

4. **Start services**:
```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

5. **Access the dashboard**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Using Docker Compose

```bash
docker-compose up --build
```

## Usage

1. Navigate to the frontend dashboard
2. Upload a research paper PDF or provide an arXiv URL
3. Click "Start Reproduction"
4. Watch the live pipeline execution
5. Review the final reproducibility report

## MVP Scope

The MVP targets **classical ML papers** with:
- Small neural networks or traditional ML algorithms
- Tabular or small image datasets
- Training that completes within minutes
- Clearly defined architectures and hyperparameters

Examples:
- Logistic regression with regularization
- Small feedforward networks
- Simple CNNs on MNIST/CIFAR-10
- Classical clustering algorithms

## Project Structure

```
/
├── backend/              # Python FastAPI backend
│   ├── agents/          # 5 autonomous agents
│   ├── orchestration/   # Pipeline and retry logic
│   ├── sandbox/         # Docker sandbox
│   ├── models/          # Pydantic schemas
│   ├── services/        # Gemini, storage, PDF processing
│   └── api/             # REST and WebSocket endpoints
├── frontend/            # React dashboard
├── generated/           # Generated code workspace
├── sandbox/             # Sandbox execution artifacts
├── storage/             # Local SQLite and logs
├── tests/               # Unit and integration tests
├── docker/              # Docker configuration
└── docs/                # Documentation
```

## Security

All generated code executes in isolated Docker containers with:
- Non-root execution
- Filesystem isolation
- CPU and memory limits
- Network restrictions
- Execution timeouts
- No access to host system or credentials

## Development

### Running Tests
```bash
cd backend
pytest tests/
```

### Code Quality
```bash
# Format
black backend/

# Type checking
mypy backend/

# Linting
ruff check backend/
```

## Deployment

See [docs/deployment.md](docs/deployment.md) for Google Cloud deployment instructions.

## Contributing

This is a hackathon project. Contributions focused on:
- Supporting more paper types
- Improving parser accuracy
- Better sandbox isolation
- Enhanced retry logic
- Cloud deployment optimization

## License

MIT

## Acknowledgments

Built with Google Gemini, Google ADK, and Google Cloud Platform.
