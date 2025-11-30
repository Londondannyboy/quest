# Quest Memory Architecture: ZEP + SuperMemory Hybrid

## Overview

Quest uses a **hybrid memory architecture** that combines two complementary systems:

| System | Purpose | Data Type |
|--------|---------|-----------|
| **ZEP** | Knowledge Graph | Structured facts, entities, relationships |
| **SuperMemory** | User Memory | Preferences, history, personalization |

```
                    ┌─────────────────────────────────────────┐
                    │           Voice/Chat Query              │
                    └─────────────────┬───────────────────────┘
                                      │
                    ┌─────────────────▼───────────────────────┐
                    │         Context Assembly                 │
                    │                                          │
                    │  ┌──────────────┐  ┌──────────────────┐ │
                    │  │  SuperMemory │  │       ZEP        │ │
                    │  │              │  │                  │ │
                    │  │ User prefs   │  │ Knowledge graph  │ │
                    │  │ Past context │  │ Country facts    │ │
                    │  │ Family info  │  │ Article content  │ │
                    │  │ Work type    │  │ Entity relations │ │
                    │  └──────────────┘  └──────────────────┘ │
                    │         │                   │            │
                    │         └────────┬──────────┘            │
                    │                  │                       │
                    │         ┌────────▼────────┐              │
                    │         │  Neon Fallback  │              │
                    │         │ (if ZEP empty)  │              │
                    │         └─────────────────┘              │
                    └─────────────────┬───────────────────────┘
                                      │
                    ┌─────────────────▼───────────────────────┐
                    │         Gemini LLM Response             │
                    └─────────────────┬───────────────────────┘
                                      │
                    ┌─────────────────▼───────────────────────┐
                    │         Post-Response Storage           │
                    │                                          │
                    │  ┌──────────────┐  ┌──────────────────┐ │
                    │  │  SuperMemory │  │       ZEP        │ │
                    │  │  Store turn  │  │ Thread messages  │ │
                    │  │  Extract     │  │                  │ │
                    │  │  preferences │  │                  │ │
                    │  └──────────────┘  └──────────────────┘ │
                    └─────────────────────────────────────────┘
```

## ZEP: Knowledge Graph

**Purpose**: Structured knowledge about relocation topics

### What ZEP Stores
- **Countries**: Facts, visa info, cost of living
- **Articles**: Guide content, excerpts, metadata
- **Entities**: Locations, companies, people
- **Relationships**: Entity connections (LOCATED_IN, MENTIONS, etc.)

### ZEP Graphs
```
ZEP_GRAPH_ID_FINANCE    = "finance-knowledge"  # Placement, PE news
ZEP_GRAPH_ID_RELOCATION = "relocation"         # Relocation guides
ZEP_GRAPH_ID_JOBS       = "jobs"               # Job market
```

### When to Use ZEP
- "What visa do I need for Cyprus?"
- "Tell me about cost of living in Portugal"
- "What countries have digital nomad visas?"

---

## SuperMemory: User Memory

**Purpose**: Personalized context for individual users

### What SuperMemory Stores
- **Preferences**: Destination interests, budget, priorities
- **Context**: Origin location, family situation, work type
- **History**: Past conversation summaries
- **Extracted Info**: Structured preferences from conversations

### Memory Types
```python
memory_type = "conversation"  # Full exchange
memory_type = "preference"    # Extracted preference
```

### Container Tags
```python
containerTag = f"user-{user_id}"  # Per-user isolation
```

### When SuperMemory Helps
- User says "I live in DC" → Remember origin
- User mentions "my wife and kids" → Remember family
- User asks about Cyprus, then Portugal → Remember interest path
- Returning user → "Welcome back! Still looking at Cyprus?"

---

## Integration Flow

### 1. Query Processing

```python
async def process_query(query, thread_id, user_id):
    # 1. Get SuperMemory context (user personalization)
    supermemory_context = await memory_manager.get_personalized_context(
        user_id=user_id,
        current_query=query
    )

    # 2. Get ZEP thread context (conversation memory)
    zep_memory_context = zep_client.thread.get_user_context(thread_id)

    # 3. Search ZEP knowledge graph
    kg_results = await zep_graph.search(query)

    # 4. Fallback to Neon if ZEP empty
    if not kg_results:
        neon_results = await neon_store.search(query)

    # 5. Generate response with all context
    prompt = f"{system_prompt}{supermemory_context}{zep_context}{knowledge_context}"
    response = gemini.generate(prompt)

    # 6. Store in both systems
    await memory_manager.store_conversation_turn(user_id, query, response)
    zep_client.thread.add_messages(thread_id, messages)
```

### 2. Context Assembly Order

The LLM prompt includes context in this order:
1. **System prompt** - Role and behavior guidelines
2. **SuperMemory context** - User preferences and history
3. **ZEP thread context** - Recent conversation memory
4. **User question** - Current query
5. **Knowledge context** - Relevant facts from ZEP/Neon

---

## Extracted User Information

When users mention preferences, we extract and store:

| Phrase Pattern | Extracted Field | Example |
|---------------|-----------------|---------|
| "move to [country]" | `destination` | "Cyprus" |
| "I live in [place]" | `origin` | "London" |
| "my wife/kids/family" | `family` | "with children" |
| "digital nomad/remote" | `work_type` | "remote/digital nomad" |

```python
extracted_info = {
    "destination": "Cyprus",
    "origin": "London",
    "family": "with children",
    "work_type": "remote/digital nomad"
}
```

---

## API Configuration

### Environment Variables
```bash
# ZEP (Knowledge Graph)
ZEP_API_KEY=z_xxx
ZEP_GRAPH_ID=relocation

# SuperMemory (User Memory)
SUPERMEMORY_API_KEY=sm_xxx
```

### Health Check Response
```json
{
  "zep": {
    "configured": true,
    "client_ready": true,
    "purpose": "knowledge_graph"
  },
  "supermemory": {
    "configured": true,
    "client_ready": true,
    "purpose": "user_personalization"
  }
}
```

---

## Cost & Latency Comparison

| Aspect | ZEP | SuperMemory |
|--------|-----|-------------|
| **Pricing** | Per-seat + usage | Per-document + search |
| **Latency** | ~100-300ms (graph search) | ~50-150ms (semantic search) |
| **Storage** | Graph nodes + edges | Documents |
| **Best For** | Structured facts | Unstructured memory |
| **Query Type** | Entity/relationship | Semantic similarity |

### Optimization Tips
1. Run ZEP and SuperMemory searches in parallel
2. Cache frequent ZEP queries
3. Limit SuperMemory results to top 3-5
4. Store only meaningful conversations (not greetings)

---

## Migration Path

If considering a full switch to SuperMemory:

### Keep in ZEP
- Entity relationships (Company → Person → Deal)
- Temporal validity (fact freshness)
- Graph visualization
- Cross-entity queries

### Could Move to SuperMemory
- Article content storage
- Simple fact retrieval
- User conversation history

### Recommendation
**Keep both** - they serve different purposes and complement each other well.
