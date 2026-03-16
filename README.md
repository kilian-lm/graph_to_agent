# Graph-to-Agent

**Visual Agent Orchestration Framework for LLM Workflows**

Build multi-agent LLM systems using graph-based visual programming. Wire up agents visually, define message flows, and execute complex AI workflows with reproducible results.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](LICENSE)

---

## Quick Start

```bash
pip install -e .
```

```python
from graph_to_agent import GraphOrchestrator

orchestrator = GraphOrchestrator()

graph = {
    "nodes": [
        {"id": "1", "label": "user"},
        {"id": "2", "label": "Translate to French"},
        {"id": "3", "label": "system"},
        {"id": "4", "label": "I am a translator."},
    ],
    "edges": [
        {"from": "1", "to": "2"},
        {"from": "2", "to": "3"},
        {"from": "3", "to": "4"},
    ]
}

# Convert to GPT messages
messages = orchestrator.graph_to_messages(graph)

# Execute (requires OPENAI_API_KEY)
response = orchestrator.execute(graph)
```

---

## Installation Options

```bash
# Core only
pip install -e .

# With specific backends
pip install -e ".[neo4j]"      # Neo4j graph database
pip install -e ".[redis]"      # Redis Streams messaging
pip install -e ".[mem0]"       # Mem0 memory layer
pip install -e ".[hydradb]"    # HydraDB context infrastructure

# Bundles
pip install -e ".[graph]"      # Neo4j + Redis
pip install -e ".[memory]"     # Mem0 + HydraDB
pip install -e ".[all]"        # Everything
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Graph-to-Agent                          │
├─────────────────────────────────────────────────────────────┤
│  Orchestration    │  Persistence   │  Memory    │ Messaging │
│  ───────────────  │  ────────────  │  ───────── │ ───────── │
│  GraphOrchestrator│  Neo4jHandler  │  Mem0      │ Redis     │
│  EngineRoom       │  FileStore     │  HydraDB   │ Streams   │
│  GraphTranslator  │  InMemoryStore │            │           │
└─────────────────────────────────────────────────────────────┘
```

---

## Modules

### Core Orchestration
```python
from graph_to_agent import GraphOrchestrator

orchestrator = GraphOrchestrator(model="gpt-4o")
response = orchestrator.execute(graph, variables={"input": "Hello"})
```

### Persistence (Neo4j)
```python
from graph_to_agent.persistence import Neo4jHandler

db = Neo4jHandler()  # Uses NEO4J_URI, NEO4J_PASSWORD
db.save_graph_data(graph, "my_graph")
db.find_root_nodes("my_graph")      # Native Cypher
db.find_path("my_graph", "a", "b")  # Shortest path
```

### Messaging (Redis Streams)
```python
from graph_to_agent.messaging import RedisStreamsHandler

streams = RedisStreamsHandler()  # Uses REDIS_HOST
streams.publish("agent_events", {"agent": "a1", "action": "complete"})

for msg_id, msg in streams.subscribe("agent_events"):
    print(msg)
```

### Memory (Mem0)
```python
from graph_to_agent.memory import Mem0Handler

mem = Mem0Handler()  # Local or use_managed=True
mem.add_memory(messages, user_id="user_123")
memories = mem.search("preferences", user_id="user_123")

# Inject memories into LLM context
enhanced = mem.inject_memory_context(messages, user_id="user_123")
```

### Context (HydraDB)
```python
from graph_to_agent.memory import HydraDBHandler

hydra = HydraDBHandler()  # Uses HYDRADB_API_KEY
hydra.index_document("Agent docs...", metadata={"v": "1.0"})
hydra.store_agent_state("agent_1", "graph_1", state={...})

# Git-like: get state at point in time
state = hydra.get_agent_state("agent_1", timestamp="2024-01-15T10:00:00Z")
history = hydra.get_state_history("agent_1")
```

---

## Project Structure

```
graph_to_agent/
├── README.md
├── LICENSE
├── SECURITY.md
├── pyproject.toml
├── Makefile
├── app.py                    # Flask web app
│
├── src/graph_to_agent/       # Main package
│   ├── core/                 # Orchestration
│   │   ├── orchestrator.py
│   │   ├── engine.py
│   │   └── translator.py
│   ├── agents/               # LLM backends
│   │   └── openai.py
│   ├── persistence/          # Storage
│   │   ├── neo4j_handler.py
│   │   ├── file.py
│   │   └── memory.py
│   ├── messaging/            # Pub/Sub
│   │   └── redis_streams.py
│   └── memory/               # AI Memory
│       ├── mem0_handler.py
│       └── hydra_handler.py
│
├── controllers/              # Legacy Flask controllers
├── functions/                # Firebase Cloud Functions
├── templates/                # HTML templates
├── static/                   # JS/CSS
├── examples/                 # Usage examples
├── tests/                    # Test suite
├── docs/                     # Documentation
│   ├── GRAPH_TO_AGENT_VS_MIROFISH.md
│   ├── LINKEDIN_RESPONSE.md
│   ├── README_FIREBASE.md
│   └── audit/
├── scripts/                  # Deployment scripts
└── legacy/                   # Deprecated code
```

---

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Neo4j (optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=...

# Redis (optional)
REDIS_HOST=localhost
REDIS_PASSWORD=...

# Mem0 (optional, for managed)
MEM0_API_KEY=...

# HydraDB (optional)
HYDRADB_API_KEY=...
```

---

## Comparison with Other Tools

| Tool | Focus | Use When |
|------|-------|----------|
| **Graph-to-Agent** | Visual orchestration | Reproducible expert workflows |
| **Mirofish** | Emergent simulation | Futures forecasting |
| **Mem0** | Memory persistence | Personalized AI |
| **HydraDB** | Temporal context | Enterprise audit trails |

See [docs/GRAPH_TO_AGENT_VS_MIROFISH.md](docs/GRAPH_TO_AGENT_VS_MIROFISH.md) for detailed comparison.

---

## Development

```bash
make dev        # Install with dev dependencies
make test       # Run tests
make lint       # Lint code
make run        # Run Flask app
```

---

## Vision

Graph-to-Agent implements the "Wire-Box" concept from the original [Beacon of Git proposal](https://www.linkedin.com/pulse/proposal-re-use-re-design-flawed-reward-system-git-all-kilian-lehn-oj2ze/):

> "Users can segment their thought processes, encapsulate them within agents, and interlink them. These agents aren't just isolated data points—they're interconnected facets of your understanding."

See [READ_ME/Vision.md](READ_ME/Vision.md) for the full vision.

---

## Links

- [YouTube Demo (2023)](https://www.youtube.com/watch?v=NFA_c7bbALM)
- [Original Vision Article](https://www.linkedin.com/pulse/proposal-re-use-re-design-flawed-reward-system-git-all-kilian-lehn-oj2ze/)
- [Security Policy](SECURITY.md)

---

## License

[GPL-3.0](LICENSE)
