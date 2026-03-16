# Graph-to-Agent: Open Source Audit & State-of-the-Art Roadmap

**Audit Date:** 2026-03-15
**Auditor:** Claude Code (Opus 4.5)
**Repository:** `graph_to_agent`
**Branch:** `kl-dev-general`

---

## Executive Summary

This document provides a comprehensive security audit, architectural analysis, and roadmap for making `graph_to_agent` a production-ready, state-of-the-art open-source agent framework.

**Key Finding:** The repository is **SAFE for open-sourcing** with no critical credential leaks detected.

---

## 1. Security Audit Results

### 1.1 Credential Scan Results

| Check | Status | Details |
|-------|--------|---------|
| Hardcoded API Keys (sk-*, ghp_*, AIza*) | PASS | No hardcoded keys found |
| Environment Variable Pattern | PASS | All secrets use `os.getenv()` |
| .env Files Committed | PASS | None found in repo |
| Private Keys (.pem, .key) | PASS | None found |
| Service Account JSON | PASS | Not committed, loaded via env |
| Git History Secret Scan | PASS | No leaked secrets in history |
| Notebooks Output Scan | PASS | Placeholder values only (`'************************'`) |

### 1.2 Files Reviewed for Secrets

```
controllers/CloudRunSpecificInMemoryOpenAiKeyHandling.py  - SAFE (runtime storage only)
controllers/EngineRoom.py                                 - SAFE (env vars)
controllers/BigQueryHandler.py                            - SAFE (env vars)
controllers/AnswerPatternProcessor.py                     - SAFE (env vars)
app.py                                                    - SAFE (env vars)
audio_graph_app.py                                        - SAFE (env vars)
data_science/*.ipynb                                      - SAFE (placeholders)
```

### 1.3 Sensitive Files in .gitignore

The following sensitive patterns are correctly ignored:
- `*.env` - Environment files
- `*.json` - Service account credentials
- `privat_chat_hist/` - Private chat history
- `*.log` - Log files

### 1.4 Recommendations Before Open-Sourcing

| Priority | Action | Status |
|----------|--------|--------|
| HIGH | Add `.idea/` to `.gitignore` | **TODO** |
| MEDIUM | Remove `*.xml` from gitignore (IDE files should be ignored, not XML data) | Review |
| LOW | Add `SECURITY.md` with disclosure policy | **TODO** |
| LOW | Add pre-commit hooks for secret scanning | **TODO** |

---

## 2. Architecture Overview

### 2.1 Core Concept

**Graph-to-Agent** is a visual agent orchestration framework that:
1. Allows users to visually construct agent communication graphs using vis.js
2. Translates graph structures into GPT-compatible message sequences
3. Executes multi-agent conversations with message passing
4. Stores and retrieves graph executions via BigQuery

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface (vis.js)                  │
│                    ┌───────────────────┐                     │
│                    │   Graph Editor    │                     │
│                    │  nodes + edges    │                     │
│                    └────────┬──────────┘                     │
└─────────────────────────────┼───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                      Flask Application                       │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  AppOrchestrator │──│  EngineRoom      │                 │
│  └────────┬─────────┘  └────────┬─────────┘                 │
│           │                     │                            │
│  ┌────────▼─────────┐  ┌────────▼─────────┐                 │
│  │ GraphPattern     │  │ GptAgentInteract │                 │
│  │ Processor        │  │     ions         │                 │
│  └────────┬─────────┘  └────────┬─────────┘                 │
└───────────┼─────────────────────┼───────────────────────────┘
            │                     │
┌───────────▼─────────────────────▼───────────────────────────┐
│                   External Services                          │
│   ┌───────────┐    ┌───────────┐    ┌───────────┐          │
│   │  OpenAI   │    │  BigQuery │    │  Firebase │          │
│   │   API     │    │   (GCP)   │    │  Hosting  │          │
│   └───────────┘    └───────────┘    └───────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Key Components

| Component | File | Purpose |
|-----------|------|---------|
| **AppOrchestrator** | `controllers/AppOrchestrator.py` | Main orchestration layer |
| **EngineRoom** | `controllers/EngineRoom.py` | Tree-to-GPT translation |
| **GraphPatternProcessor** | `controllers/GraphPatternProcessor.py` | Graph structure processing |
| **MatrixLayerOne** | `controllers/MatrixLayerOne.py` | Adjacency matrix generation |
| **AnswerPatternProcessor** | `controllers/AnswerPatternProcessor.py` | Response pattern handling |
| **BigQueryHandler** | `controllers/BigQueryHandler.py` | Persistence layer |

### 2.3 Data Flow

1. **Input**: User creates graph with `user`, `system`, and content nodes
2. **Translation**: Graph edges define message sequence (`user → content → system`)
3. **Execution**: Multi-agent chains with `@variable` substitution
4. **Storage**: Results persisted to BigQuery with timestamps
5. **Output**: Augmented graph with agent responses as new nodes

---

## 3. Comparison: Graph-to-Agent vs. Mirofish

### 3.1 Architectural Comparison

| Feature | Graph-to-Agent (2023) | Mirofish (2026) |
|---------|----------------------|-----------------|
| **Core Paradigm** | Visual graph → LLM prompts | Seed → Agent simulation |
| **Agent Model** | Explicit message passing via edges | Emergent behavior from simulated agents |
| **Simulation** | Single-pass multi-agent execution | Continuous "digital world" simulation |
| **UI Approach** | vis.js graph editor | Seed-based input |
| **Persistence** | BigQuery (structured) | Unknown |
| **Scale** | Small agent pools (<100) | "Thousands of AI agents" |

### 3.2 Philosophical Difference

**Graph-to-Agent (Your Approach - 2023)**:
- **Deterministic orchestration**: Users explicitly wire agent communication
- **Reproducible**: Same graph = same execution path
- **Expert-driven**: "Wire-Box" approach for domain experts to encode knowledge
- **Git-like versioning**: Content evolution graphs with version control

**Mirofish (2026)**:
- **Emergent behavior**: Agents interact freely, patterns surface
- **Simulation-first**: "Futures sandbox" for scenario planning
- **Probabilistic**: Each run may yield different emergent patterns
- **God's-eye view**: Observe and inject variables into simulation

### 3.3 Your Unique Value Proposition

Your 2023 work anticipated several concepts that Mirofish now implements:

| Your Concept (2023) | Mirofish Equivalent (2026) |
|---------------------|---------------------------|
| "Wire-Box" agent layering | Agent personality/behavioral logic |
| `@variable` substitution | Variable injection |
| Message passing protocols | Agent interaction dynamics |
| Graph-based agent composition | Entity relationship extraction |
| "Conway's Game of Life" simulation | Emergent pattern observation |

**Your differentiator**: **Explicit, reproducible, versionable agent orchestration** vs. Mirofish's emergent simulation.

---

## 4. Open Source Packaging Roadmap

### 4.1 Package Structure (Proposed)

```
graph_to_agent/
├── pyproject.toml              # Modern Python packaging
├── setup.cfg                   # Package metadata
├── README.md                   # Updated with badges/quickstart
├── LICENSE                     # GPL-3.0 (already present)
├── SECURITY.md                 # Security policy
├── CHANGELOG.md                # Version history
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              # Lint + Test
│   │   ├── release.yml         # PyPI publish
│   │   └── security.yml        # Secret scanning
│   └── ISSUE_TEMPLATE/
├── src/
│   └── graph_to_agent/
│       ├── __init__.py
│       ├── core/
│       │   ├── orchestrator.py
│       │   ├── engine.py
│       │   └── translator.py
│       ├── agents/
│       │   ├── base.py
│       │   ├── openai.py
│       │   └── anthropic.py    # Add Claude support
│       ├── persistence/
│       │   ├── bigquery.py
│       │   └── sqlite.py       # Local alternative
│       └── web/
│           ├── app.py
│           ├── static/
│           └── templates/
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
│   ├── quickstart.md
│   ├── architecture.md
│   └── api/
└── examples/
    ├── basic_agent_chain.py
    └── expert_wirebox.py
```

### 4.2 pyproject.toml (Proposed)

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "graph-to-agent"
version = "0.2.0"
description = "Visual agent orchestration framework for LLM workflows"
readme = "README.md"
license = {text = "GPL-3.0"}
authors = [
    {name = "Kilian Lehn", email = "your@email.com"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]
keywords = ["agents", "llm", "openai", "graph", "orchestration", "multi-agent"]
requires-python = ">=3.10"
dependencies = [
    "flask>=2.0.0",
    "openai>=1.0.0",
    "google-cloud-bigquery>=3.0.0",
    "python-dotenv>=1.0.0",
    "networkx>=3.0",
    "requests>=2.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
    "pre-commit>=3.0",
]
anthropic = ["anthropic>=0.20.0"]
all = ["graph-to-agent[dev,anthropic]"]

[project.urls]
Homepage = "https://github.com/kilian-lm/graph_to_agent"
Documentation = "https://graph-to-agent.readthedocs.io"
Repository = "https://github.com/kilian-lm/graph_to_agent"

[project.scripts]
graph-to-agent = "graph_to_agent.cli:main"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --cov=src/graph_to_agent"
```

### 4.3 CI/CD Configuration (`.github/workflows/ci.yml`)

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install ruff
      - run: ruff check .

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: pytest --cov

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: TruffleHog Secret Scan
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
```

---

## 5. Immediate Actions

### 5.1 Pre-Open-Source Checklist

```bash
# 1. Add .idea to .gitignore
echo ".idea/" >> .gitignore

# 2. Remove any tracked .idea files
git rm -r --cached .idea/

# 3. Create SECURITY.md
cat > SECURITY.md << 'EOF'
# Security Policy

## Reporting a Vulnerability

Please report security vulnerabilities to [your-email] with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

We aim to respond within 48 hours.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |
EOF

# 4. Install pre-commit hooks for secret scanning
pip install pre-commit detect-secrets
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
EOF
detect-secrets scan > .secrets.baseline
pre-commit install
```

### 5.2 Quick Wins for "Pro-Level"

| Action | Impact | Effort |
|--------|--------|--------|
| Add type hints to core modules | High | Medium |
| Add basic pytest coverage | High | Medium |
| Create `examples/` directory | High | Low |
| Add Anthropic Claude support | High | Low |
| Add SQLite persistence option | Medium | Medium |
| Create Docker Compose for local dev | Medium | Low |

---

## 6. LinkedIn Response Context

### Your Historical Priority Claim

Based on the YouTube video referenced (2023-12-10) and the commit history, you can legitimately claim:

> "I built a graph-based agent orchestration framework in 2023 that allows visual composition of LLM agent workflows. The concepts of explicit agent wiring, message passing protocols, and versioned content graphs anticipated what Mirofish is now doing with emergent simulation. Different approaches to the same problem - mine focuses on reproducibility and expert control, theirs on emergent discovery."

### Key Differentiators to Highlight

1. **Visual Agent Wiring**: Your vis.js editor for explicit agent composition
2. **Reproducibility**: Same graph = same execution path (vs. emergent simulation)
3. **Expert Wire-Box**: Domain experts encode knowledge in reusable agent pools
4. **Git-like Versioning**: Content evolution tracking built-in
5. **Open Source**: GPL-3.0 licensed, transparent implementation

---

## 7. Conclusion

**Security Status**: READY for open source
**Code Quality**: Functional MVP, needs refactoring for production
**Packaging**: Needs modern Python packaging (pyproject.toml)
**Documentation**: Vision.md is excellent, needs API docs
**Competitive Position**: Complementary to Mirofish (control vs. emergence)

Your 2023 work is a valid precursor to the 2026 agent simulation wave. The architectural choice of explicit graph-based orchestration vs. emergent simulation is a design decision, not a gap.

---



