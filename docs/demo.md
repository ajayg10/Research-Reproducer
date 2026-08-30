# Demo Script for Hackathon Presentation

## Overview
This demo showcases the **Autonomous Research Reproducibility Engine** — a system that goes beyond code generation to actually execute and empirically verify research paper reproduction.

**Duration**: 8-10 minutes

## Key Differentiator
> "Most AI coding assistants stop at generating code. We execute it, capture metrics, and empirically verify if the reproduction matches the paper."

---

## Demo Flow

### 1. Introduction (1 minute)

**Script**:
"Traditional research reproducibility is manual and time-consuming. Researchers spend weeks:
- Reading papers
- Writing code
- Debugging
- Running experiments
- Comparing results

Our system automates this entire pipeline. Watch what happens when we upload a research paper."

---

### 2. Upload Paper (30 seconds)

**Actions**:
- Open frontend dashboard: http://localhost:5173
- Show clean, simple interface
- Select demo paper PDF (prepare a simple ML paper in advance)
- Click "Start Reproduction"

**Script**:
"I'm uploading a paper on [X algorithm/model]. Notice we're not just asking for a summary — we're starting an autonomous reproduction pipeline."

**Show**: Pipeline ID generated, redirect to pipeline page

---

### 3. Live Pipeline Execution (3-4 minutes)

**Actions**:
- Show live pipeline visualization with 5 stages
- Highlight real-time status updates via WebSocket

**Script for each stage**:

**PARSING** (⟳ in progress):
"The Parser agent is extracting the technical specification from the PDF using Gemini.

It's identifying:
- Model architecture
- Hyperparameters
- Dataset requirements
- Reported metrics

Notice it explicitly marks ambiguous information — not all papers specify everything clearly."

**PLANNING** (✓ completed → ⟳ in progress):
"The Planner agent creates a concrete implementation plan.

It determines:
- Project structure
- Python dependencies
- Training loop design
- Reproducibility requirements like random seeds

It distinguishes what's explicitly in the paper versus what must be inferred."

**GENERATING** (✓ completed → ⟳ in progress):
"The Codegen agent is writing the actual implementation.

Watch this — we'll see the generated code appear on screen in real-time."

**Show**: Generated code viewer with multiple files
- model.py
- dataset.py
- train.py
- requirements.txt

**Script**:
"Seven files generated. This is executable code, not pseudocode. Let's see what happens next."

**EXECUTING** (✓ completed → ⟳ in progress):
"Here's the critical difference. The Executor agent is running this code **right now** in an isolated Docker sandbox.

The sandbox has:
- Resource limits (CPU, memory)
- Network isolation
- Timeout protection
- Non-root execution

The system is training the model and capturing metrics. You can see stdout streaming live."

**Show**: Execution logs appearing in real-time

**VERIFYING** (✓ completed → ⟳ in progress):
"The Verifier agent compares the reproduced results with the paper's claimed metrics."

---

### 4. Results and Report (2 minutes)

**Actions**:
- Show verification report
- Highlight metrics comparison table

**Script**:
"The pipeline completed. Here's the verification report.

**Metrics Comparison Table**:
- Paper claimed accuracy: 94.2%
- Our reproduction: 93.1%
- Difference: 1.1% (within 2% tolerance)
- Status: PASS

**Overall Verdict**: PARTIAL REPRODUCIBILITY

Why partial? One metric passed, but there's a discrepancy in F1 score. The system identified the likely cause: the paper didn't fully specify the data preprocessing steps.

This is the key insight — we didn't just generate code, we empirically verified it matches the paper."

---

### 5. Show Retry Mechanism (1 minute)

**Optional if time permits**:

**Script**:
"Let me show you something else powerful. When code fails, the system automatically retries.

[Show pipeline with retry_count > 0]

The system:
1. Detected the execution failure
2. Analyzed the error type
3. Decided a retry was appropriate
4. Re-executed the code
5. Successfully completed on attempt 2

All of this happened autonomously while you watched."

---

### 6. Architecture Highlight (1 minute)

**Actions**:
- Switch to architecture diagram (prepared slide or docs/architecture.md)

**Script**:
"How does this work?

Five autonomous agents orchestrated in a pipeline:
1. **Parser** → Extracts structured specs with Gemini
2. **Planner** → Creates implementation plan
3. **Codegen** → Generates executable code
4. **Executor** → Runs in Docker sandbox
5. **Verifier** → Compares results

Every agent's output is validated. Failures trigger retries. The entire state is persisted and observable.

We use:
- **Google Gemini** for LLM operations
- **Google ADK** for orchestration
- **Docker** for secure execution
- **Cloud Run** for deployment

---

### 7. Closing (30 seconds)

**Script**:
"This system closes the loop from paper to verified implementation.

It doesn't just tell you **how** to reproduce research — it actually **does** the reproduction and tells you if it worked.

This can accelerate:
- Research validation
- Paper reviews
- Reimplementing baselines
- Teaching reproducibility

Thank you. Questions?"

---

## Demo Preparation Checklist

### Before Demo

- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:5173
- [ ] Docker daemon running
- [ ] Python sandbox image pulled: `docker pull python:3.11-slim`
- [ ] Demo paper PDF ready (simple ML, ~5min execution)
  - Suggested: Logistic regression, small neural network, or scikit-learn algorithm
- [ ] Test complete pipeline flow at least once
- [ ] Clear old pipelines if showing fresh interface
- [ ] Internet connection stable (for Gemini API)
- [ ] Gemini API key valid and working

### Demo Paper Requirements

The demo paper should:
- Be a classical ML paper (not deep learning with GPUs)
- Have clearly stated hyperparameters
- Use a small, standard dataset (MNIST, Iris, etc.)
- Complete training in < 5 minutes
- Report 1-3 metrics (accuracy, loss, F1)

**Example Papers** (or synthesize one):
- "Logistic Regression with L2 Regularization on Iris Dataset"
- "Simple Neural Network for MNIST Digit Classification"
- "K-Means Clustering Evaluation on Synthetic Data"

### Backup Plan

If live demo fails:
- Have a pre-recorded screen capture ready
- Have screenshots of each pipeline stage
- Have a completed pipeline you can show in the dashboard

### Practice

- Rehearse the script at least 3 times
- Time each section
- Prepare for common questions (see below)

---

## Expected Questions & Answers

**Q: How long does a typical pipeline take?**
A: For the MVP (simple ML), 5-10 minutes. For complex deep learning, it could take hours — we'd move that to GKE with GPU support.

**Q: What if the paper has missing information?**
A: The Parser marks it as ambiguous. The Planner documents assumptions. The Verifier flags it as a potential discrepancy source. The report tells you what couldn't be reproduced faithfully.

**Q: Can it handle any research paper?**
A: Not yet. The MVP targets classical ML. We're working toward supporting:
- Deep learning with GPU
- Custom datasets
- Multi-day training
- Distributed training

**Q: How accurate is the reproduction?**
A: It depends on paper clarity. For well-specified papers, we see high fidelity. For vague papers, we document gaps. That's actually valuable information.

**Q: What about security?**
A: All generated code runs in isolated Docker containers with:
- No network access
- Resource limits
- Timeout enforcement
- Non-root execution
- No access to host system or credentials

**Q: How much does it cost to run?**
A: MVP on Google Cloud: ~$20-80/month depending on usage. Gemini API calls are the variable cost. We can optimize with caching and batching.

**Q: Can I contribute?**
A: Yes! This is open source. We need help with:
- Supporting more paper types
- GPU execution
- Better LLM prompts for accuracy
- Dataset downloaders
- Evaluation harnesses

---

## Demo Tips

1. **Start with impact**: Lead with the problem (reproducibility crisis) and the solution (autonomous verification)

2. **Show, don't tell**: Let the live pipeline speak for itself. Don't narrate every detail.

3. **Highlight the difference**: Keep emphasizing that this executes and verifies, not just generates.

4. **Be honest about limitations**: The MVP is scoped to simple papers. That's okay — it proves the concept.

5. **Engage with failures**: If something breaks during demo, explain the retry mechanism. That's a feature, not a bug.

6. **Prepare for skepticism**: Some will say "but GPT can write code." Respond: "Can it run that code, capture metrics, and tell you if it matches the paper? That's the difference."

---

## Judging Criteria Alignment

Match your demo narrative to typical hackathon criteria:

**Innovation**: 
"First system to close the loop from paper to empirical verification"

**Technical Complexity**:
"Multi-agent orchestration, LLM structured output, secure sandboxing, stateful pipeline"

**Real-World Impact**:
"Accelerates research validation, helps paper reviews, enables reproducibility at scale"

**Execution Quality**:
"Fully working end-to-end system, deployed on Google Cloud, extensible architecture"

**Google Technology Use**:
"Gemini for LLM, ADK for orchestration, Cloud Run for deployment, Firestore for state"

---

## Post-Demo

After the demo, have ready:
- GitHub repository link
- Live deployment URL (if deployed)
- Architecture diagram
- Roadmap for future enhancements
- Contact information for judges

---

Good luck! 🚀
