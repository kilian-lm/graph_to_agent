# Graph-to-Agent vs. Mirofish: A Comparative Analysis

**Author:** Kilian Lehn
**Date:** December 2023 (original) / March 2026 (updated)
**Context:** Response to [Mirofish trending on GitHub](https://666ghj.github.io/mirofish-demo/) and the question of prior art

---

## Executive Summary

**Graph-to-Agent** (December 2023) and **Mirofish** (March 2026) represent two distinct philosophical approaches to the same fundamental problem: *How do we orchestrate multiple AI agents to model complex systems?*

| Aspect | Graph-to-Agent (2023) | Mirofish (2026) |
|--------|----------------------|-----------------|
| **Core Philosophy** | Explicit orchestration | Emergent simulation |
| **Reproducibility** | Deterministic (same graph = same path) | Probabilistic (emergent patterns) |
| **User Control** | High (visual wiring) | Low (seed-based, observe emergence) |
| **Use Case** | Expert knowledge encoding | Futures forecasting |
| **Metaphor** | "Dumbledore's Pensieve" | "Digital World Sandbox" |

---

## Historical Context

### Graph-to-Agent: "Beacon of Git" (December 2023)

Published in the LinkedIn article ["Proposal: Re-Use & Re-Design of a flawed reward system, or 'Git IS ALL YOU NEED'"](https://www.linkedin.com/pulse/proposal-re-use-re-design-flawed-reward-system-git-all-kilian-lehn-oj2ze/), the Graph-to-Agent framework emerged from a critique of modern social media's "infinite scroll" paradigm.

**Original Vision (from Vision.md):**
> "A social-network consisting of Knowledge Graphs in the form of Personal Knowledge Libraries referred to as 'Beacon of Git'. We aspire to give an alternative to the short-lived, buzzword-heavy, scrollable, swipable knowledge-transfer."

The "Wire-Box" component specifically addresses agent orchestration:
> "Users can segment their thought processes, encapsulate them within agents, and interlink them. These agents aren't just isolated data points—they're interconnected facets of your understanding. They can interact, validate, or even challenge each other based on the connections you've made."

### Mirofish (March 2026)

According to the [demo](https://666ghj.github.io/mirofish-demo/), Mirofish is described as:
> "An open-source AI prediction engine... It builds a parallel digital world. You upload a 'seed': a news report, a policy draft, a financial signal. The system extracts entities, relationships, and social dynamics, then populates a simulated environment with thousands of AI agents."

---

## Detailed Comparison

### 1. Agent Composition Model

#### Graph-to-Agent: Visual Wiring
```
User creates explicit graph:

    [user] ──> [instruction] ──> [system] ──> [response]
         \                                    /
          └──> [expert_agent_1] ──> [meta_agent]
                                        │
               [expert_agent_2] ────────┘
```

- **Explicit edges** define message flow
- **User controls** every connection
- **Reproducible**: Same graph = same execution

#### Mirofish: Emergent Simulation
```
User provides seed → System generates agents → Agents interact freely

    [Seed: "Climate policy draft"]
              │
              ▼
    ┌─────────────────────────────┐
    │   Agent Population (1000s)  │
    │   ┌───┐ ┌───┐ ┌───┐ ┌───┐  │
    │   │ A │↔│ B │↔│ C │↔│...│  │
    │   └───┘ └───┘ └───┘ └───┘  │
    │      Emergent Patterns      │
    └─────────────────────────────┘
```

- **Implicit relationships** emerge from simulation
- **System controls** agent interactions
- **Probabilistic**: Each run may differ

### 2. Reproducibility vs. Emergence

| Property | Graph-to-Agent | Mirofish |
|----------|---------------|----------|
| Same input = same output? | Yes (deterministic) | No (stochastic) |
| Can version control execution? | Yes (Git-native) | Difficult |
| Debugging | Trace graph path | Analyze simulation logs |
| Expert validation | Direct verification | Statistical validation |

**Graph-to-Agent** aligns with scientific principles:
> "By championing 'reproducibility' we want to ensure that the path to insight—each node and edge of connection—is not only transparent but navigable by others" — Vision.md

**Mirofish** embraces uncertainty:
> "Emergent behavior in agent-based models can also amplify biases present in the underlying LLMs. These are not small caveats."

### 3. Expert Knowledge Encoding

#### Graph-to-Agent: The Wire-Box Philosophy

From the original proposal:
> "We created it because we want to mine expert knowledge... The point is, if those experts don't know how to use custom instruction or how to layer agents... then we are missing an opportunity. The opportunity to uncover the traces that those expert fields left in the language corpus that GPT uses."

**Key insight**: Experts are "keys" that unlock domain-specific agent wiring patterns.

```python
# Expert-designed agent pool (reproducible)
expert_graph = {
    "nodes": [
        {"id": "skeptic", "label": "Critically examine risks"},
        {"id": "optimist", "label": "Identify opportunities"},
        {"id": "synthesizer", "label": "Balance both perspectives"},
    ],
    "edges": [
        {"from": "skeptic", "to": "synthesizer"},
        {"from": "optimist", "to": "synthesizer"},
    ]
}
```

#### Mirofish: Emergent Discovery

Mirofish takes a different approach: instead of encoding expert knowledge, it lets patterns emerge from agent interactions, which experts then interpret.

### 4. Use Cases

| Use Case | Better Fit |
|----------|------------|
| Regulatory compliance analysis | Graph-to-Agent (audit trail) |
| Policy stress-testing | Mirofish (emergent scenarios) |
| Expert knowledge capture | Graph-to-Agent (explicit encoding) |
| Geopolitical forecasting | Mirofish (complex dynamics) |
| Reproducible research | Graph-to-Agent (version control) |
| Creative exploration | Mirofish (emergent creativity) |

---

## Conceptual Overlap: What We Both Saw

Despite different approaches, both frameworks identified similar core concepts:

| Concept | Graph-to-Agent (2023) | Mirofish (2026) |
|---------|----------------------|-----------------|
| Multi-agent orchestration | Wire-Box with explicit wiring | Agent population with emergent behavior |
| Variable injection | `@variable` substitution | Seed-based variable injection |
| Message passing | Graph edges define protocol | Agents interact with memory/personality |
| Entity relationships | User-defined nodes/edges | Extracted from seed data |
| Simulation | "Conway's Game of Life" mentioned | Core simulation engine |

### Quote from Vision.md (2023):
> "We could also model the HAAS in vis.js, or we could even go for Conway's Game of Life or we could simulate different graph message protocols e.g. flooding"

This anticipated the simulation-based approach that Mirofish later implemented.

---

## The Philosophical Divide

### Graph-to-Agent: Control & Reproducibility
> "In the spirit of 'Understanding instead of judging' ('Comprendre au lieu du juger') — it is our conviction that by visualizing the intellectual trajectories of thought and discovery, we empower others to follow, comprehend, and expand upon them."
> — Albert Camus reference in Vision.md

### Mirofish: Emergence & Discovery
> "The future does not arrive as a single event. It emerges from millions of small interactions."

**Neither is "better"** — they serve different epistemological needs:
- **Graph-to-Agent**: When you need to *explain* and *reproduce*
- **Mirofish**: When you need to *explore* and *discover*

---

## Practical Recommendations

### When to Use Graph-to-Agent
1. **Expert knowledge systems** - encode domain expertise
2. **Compliance/audit** - need reproducible results
3. **Educational tools** - teach agent orchestration
4. **Version-controlled AI workflows** - Git-native approach
5. **Debugging complex prompts** - visual trace of execution

### When to Use Mirofish
1. **Scenario planning** - explore possible futures
2. **Complex system modeling** - emergent behavior matters
3. **Creative ideation** - let patterns emerge
4. **Risk discovery** - find unknown unknowns
5. **Large-scale simulations** - thousands of agents

---

## Conclusion

Graph-to-Agent and Mirofish represent complementary approaches to multi-agent AI orchestration:

- **Graph-to-Agent** (2023): Brought visual, reproducible, Git-native agent composition to non-technical experts through the "Wire-Box" paradigm.

- **Mirofish** (2026): Scaled the simulation aspect with emergent agent behavior for futures forecasting.

The December 2023 work anticipated several concepts that became central to Mirofish, but chose a different path: **explicit control over emergent discovery**.

As stated in the original proposal:
> "Every participant is both a learner and a contributor, each Personal Knowledge Library a chapter in a grander compendium of human(-agent) intellect."

Both tools can coexist in a practitioner's toolkit — one for controlled orchestration, the other for emergent exploration.

---

## References

- [Graph-to-Agent Vision](../READ_ME/Vision.md)
- [Original LinkedIn Article (December 2023)](https://www.linkedin.com/pulse/proposal-re-use-re-design-flawed-reward-system-git-all-kilian-lehn-oj2ze/)
- [YouTube Demo (December 2023)](https://www.youtube.com/watch?v=NFA_c7bbALM)
- [Mirofish Demo](https://666ghj.github.io/mirofish-demo/)
- [OpenAI Dev Day 2023 - Assistants API](https://www.youtube.com/watch?v=U9mJuUkhUzk) (referenced in original proposal)

---

*"Science is more than a body of knowledge; it's a way of thinking."*
— Carl Sagan (cited in Vision.md)
