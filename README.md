# AI-PM-Master

> An intelligent Q&A system with semantic retrieval, parameter tuning, and comprehensive evaluation framework.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Overview

AI-PM-Master is a production-ready intelligent Q&A platform featuring:

- **Semantic Retrieval (RAG)**: Uses Embedding + FAISS vector database for contextual understanding
- **Hallucination Detection**: Automated detection of AI-generated false content
- **Parameter Optimization**: Real-time tuning of Temperature, Top-p, and Max tokens
- **Evaluation Framework**: Batch evaluation with LLM-as-judge scoring
- **Cost Analytics**: Estimation and comparison of model costs
- **Function Calling**: Tool-augmented AI with visible reasoning traces
- **Microservice Architecture**: FastAPI backend for scalable evaluation services

---

## Features

### 🤖 Intelligent Q&A
- Vector-based semantic search (not simple keyword matching)
- Automatic hallucination detection with confidence scoring
- Source citation for answer traceability
- Real-time performance metrics (latency, token usage, cost)

### 🎛️ Parameter Tuning Lab
- Interactive adjustment of model parameters
- A/B testing with side-by-side comparison
- Visual impact analysis of parameter changes

### 📝 Prompt Version Management
- Version control for prompt templates
- A/B testing between different prompt versions
- Built-in templates: Base / Strict (low hallucination) / Friendly

### 📊 Evaluation Center
- Batch evaluation with CSV test sets
- LLM-as-judge automatic scoring
- Comprehensive metrics: accuracy, cost, token consumption
- Exportable evaluation reports

### 📈 Analytics Dashboard
- Core metrics: interaction volume, adoption rate, cost, latency
- Risk distribution analysis
- Data logging and export capabilities

### 💰 Cost & Latency Dashboard
- Monthly/yearly cost estimation
- Multi-model cost comparison for decision-making
- Latency analysis (P50/P90/P99 percentiles)

### 🛠️ Function Calling Demo
- Tool invocation by AI (calculator, weather, knowledge base search)
- Visible reasoning traces (ReAct pattern)
- Agent foundation demonstration

---

## Architecture

**Frontend**: Streamlit multi-page application  
**Backend**: FastAPI microservice for evaluation  
**RAG Engine**: sentence-transformers + FAISS  
**Deployment**: Docker Compose  

---

## Quick Start

### Prerequisites
- Python 3.10+
- 8GB+ RAM
- LLM API key (OpenAI / DeepSeek / Qwen / etc.)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/xhygaaaaa/AI-PM-Master.git
cd AI-PM-Master
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure API key**
```bash
cp .env.example .env
# Edit .env and set your LLM_API_KEY
```

4. **Run the application**

**Option A: Frontend only (simplest)**
```bash
streamlit run main.py
```
Open http://localhost:8501

**Option B: Frontend + Backend (full architecture)**
```bash
# Windows
start_all.bat

# Mac/Linux
./start_all.sh
```

**Option C: Docker deployment**
```bash
docker compose up
```

---

## Configuration

Edit `.env` to configure:

```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL=gpt-3.5-turbo
```

Supported APIs: OpenAI, DeepSeek, Qwen, MiniMax, local models (Ollama)

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| Backend | FastAPI |
| Embedding | sentence-transformers |
| Vector DB | FAISS |
| Visualization | Plotly |

---

## License

MIT License

---

<div align="center">

**⭐ Star this repo if you find it helpful! ⭐**

</div>
