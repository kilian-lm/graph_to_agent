# Graph-to-Agent

**Visual Agent Orchestration Framework for LLM Workflows**

Build multi-agent LLM systems using graph-based visual programming. Wire up agents visually, define message flows, and execute complex AI workflows with reproducible results.

[![CI](https://github.com/kilian-lm/graph_to_agent/actions/workflows/ci.yml/badge.svg)](https://github.com/kilian-lm/graph_to_agent/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](LICENSE)

---

## Quick Start

### Installation

```bash
# Install from source
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

### Basic Usage

```python
from graph_to_agent import GraphOrchestrator

# Initialize
orchestrator = GraphOrchestrator()

# Define a simple agent graph
graph = {
    "nodes": [
        {"id": "1", "label": "user"},
        {"id": "2", "label": "Translate the following to French"},
        {"id": "3", "label": "system"},
        {"id": "4", "label": "I am a French translator."},
        {"id": "5", "label": "user"},
        {"id": "6", "label": "Hello, how are you?"},
    ],
    "edges": [
        {"from": "1", "to": "2"},
        {"from": "2", "to": "3"},
        {"from": "3", "to": "4"},
        {"from": "4", "to": "5"},
        {"from": "5", "to": "6"},
    ]
}

# Convert to GPT messages (without API call)
messages = orchestrator.graph_to_messages(graph)
print(messages)
# [{'role': 'user', 'content': 'Translate the following to French'},
#  {'role': 'system', 'content': 'I am a French translator.'},
#  {'role': 'user', 'content': 'Hello, how are you?'}]

# Execute with OpenAI (requires OPENAI_API_KEY env var)
response = orchestrator.execute(graph)
print(response)
# "Bonjour, comment allez-vous ?"
```

### Run the Web UI

```bash
# Set your API key
export OPENAI_API_KEY=sk-...

# Run the web app
make run
# or
python -m flask --app app:app run --debug
```

Open http://localhost:5000 to use the visual graph editor.

---

## How It Works

Graph-to-Agent translates visual graphs into LLM conversation flows:

```
┌─────────────────────────────────────────────────────────┐
│                    Visual Graph                          │
│                                                          │
│    [user] ──> [instruction] ──> [system] ──> [ack]      │
│                                                          │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   GPT Messages                           │
│                                                          │
│  [{"role": "user", "content": "instruction"},            │
│   {"role": "system", "content": "ack"}]                  │
│                                                          │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    LLM Response                          │
└─────────────────────────────────────────────────────────┘
```

### Node Types

| Node Label | Purpose |
|------------|---------|
| `user` | Marks the next content as a user message |
| `system` | Marks the next content as a system message |
| *anything else* | Content to be sent as the message |

### Variable Substitution

Use `@variable` or `@variable_name` placeholders for dynamic content:

```python
graph = {
    "nodes": [
        {"id": "1", "label": "user"},
        {"id": "2", "label": "Analyze this: @variable_input"},
    ],
    "edges": [{"from": "1", "to": "2"}]
}

response = orchestrator.execute(graph, variables={"input": "Hello world"})
```

---

## Project Structure

```
graph_to_agent/
├── src/graph_to_agent/      # New clean package structure
│   ├── core/                # Core orchestration logic
│   │   ├── orchestrator.py  # Main entry point
│   │   ├── engine.py        # Low-level graph processing
│   │   └── translator.py    # Format conversions
│   ├── agents/              # LLM backends
│   │   └── openai.py        # OpenAI integration
│   ├── persistence/         # Storage backends
│   │   ├── memory.py        # In-memory storage
│   │   └── file.py          # File-based storage
│   └── web/                 # Web components
├── controllers/             # Legacy Flask controllers
├── logics/                  # Legacy business logic
├── templates/               # HTML templates
├── static/                  # JS/CSS assets
├── examples/                # Usage examples
├── tests/                   # Test suite
└── legacy/                  # Deprecated code (reference only)
```

---

## Examples

### Multi-Agent Wire-Box

The "Wire-Box" pattern lets you orchestrate multiple expert agents:

```python
# See examples/expert_wirebox.py for full code

# Agent 1: Skeptic perspective
# Agent 2: Optimist perspective
# Meta-Agent: Synthesizes both views

graph = create_multi_perspective_graph("Should we pivot to B2B?")
response = orchestrator.execute(graph)
```

### Basic Agent Chain

```python
# See examples/basic_agent_chain.py
python examples/basic_agent_chain.py
```

---

## Development

```bash
# Install dev dependencies
make dev

# Run tests
make test

# Lint and format
make lint
make format

# Run web app in debug mode
make run
```

### Environment Variables

```bash
# Required for API calls
OPENAI_API_KEY=sk-...

# Optional: BigQuery persistence
BQ_CLIENT_SECRETS='{"type":"service_account",...}'

# Optional: App configuration
GRAPH_DATASET_ID=graph_to_agent
MODEL=gpt-3.5-turbo
```

---

## Architecture Concepts

### Graph-Based Agent Composition

Unlike black-box agent frameworks, Graph-to-Agent provides:

- **Visual Composition**: Wire up agents using a graph editor
- **Reproducibility**: Same graph = same execution path
- **Versioning**: Track graph evolution like code
- **Expert Wire-Boxes**: Domain experts encode knowledge in reusable patterns

### Comparison with Emergent Simulation (e.g., Mirofish)

| Graph-to-Agent | Emergent Simulation |
|----------------|---------------------|
| Explicit orchestration | Emergent behavior |
| Reproducible results | Probabilistic outcomes |
| Expert-driven design | Simulation-based discovery |
| Version control friendly | Dynamic state |

Both approaches are valid - choose based on your needs.

---

## Vision

For the full vision and motivation, see [READ_ME/Vision.md](READ_ME/Vision.md).

**TL;DR**: Build a "Git for Knowledge" - version-controlled, graph-based knowledge libraries that enable reproducible intellectual exploration and expert knowledge encoding.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Make your changes
4. Run tests (`make test`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing`)
7. Open a Pull Request

---

## License

[GPL-3.0](LICENSE)

---

## Links

- [YouTube Demo (2023)](https://www.youtube.com/watch?v=NFA_c7bbALM)
- [Vision Document](READ_ME/Vision.md)
- [Security Policy](SECURITY.md)
