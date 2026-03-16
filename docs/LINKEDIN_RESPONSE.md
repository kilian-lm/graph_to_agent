Sotiris Melioumis MB & Dimitris Dimitriadis

Exactly the discussion we need.

Sotiris: prediction ≠ simulation. Dimitris clarified he used "futures sandbox" — not "prediction engine." Important distinction.

-- Why it matters --

Prediction: causal structure, quantified uncertainty, reproducible.
Simulation: plausible futures, "what if" exploration, hypothesis generation.

Both valuable — different purposes.

-- The Graph Perspective --

Closed World (CWA): Unknown = FALSE. Databases, planning. Deterministic. "Don't know it → not true."

Open World (OWA): Unknown = UNKNOWN. Semantic Web, LLMs. Probabilistic. "Don't know it → don't know."

LLMs are OWA — great for exploration, tricky for prediction. They fill gaps with "plausible" content.

-- Tools --

Graph-to-Agent (2023) — CWA. What you wire runs. Reproducible.
HydraDB — Hybrid. Git-like temporal history.
Mem0 — OWA. Always learning.
Mirofish — OWA. Futures sandbox.

-- Modern stack alternatives --

Storage: Neo4j / FalkorDB instead of BigQuery (native graph queries, Cypher)
Messaging: Redis Streams / NATS instead of legacy Pub/Sub (lightweight, agent-native)

-- Ideal pipeline --

CWA scaffold + OWA exploration + validation = rigorous foresight.

Kudos to both for clarity and open dialogue.

--

Mirofish: https://666ghj.github.io/mirofish-demo/
Mem0: https://github.com/mem0ai/mem0
HydraDB: https://hydradb.com/
Graph-to-Agent: https://github.com/kilian-lm/graph_to_agent
Neo4j: https://neo4j.com/
FalkorDB: https://www.falkordb.com/
