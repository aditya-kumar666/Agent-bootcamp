# Step-by-Step Educational Plan: ChromaDB RAG Knowledge Base for Review Agent

This plan is structured into **5 sequential, individually testable phases**. Each phase focuses on one core concept, builds a concrete component, and includes a verification checkpoint before proceeding.

---

## 🧭 Roadmap Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Knowledge Corpus Creation & Rule Design            │
│ └── Write curated guidelines with explicit Rule IDs & tags  │
│ └── Checkpoint: Validate document structure & parsing       │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ Phase 2: ChromaDB Ingestion & Hybrid Retrieval Service       │
│ └── Build KnowledgeService: chunking, metadata, vector DB   │
│ └── Checkpoint: Test semantic search & domain filtering     │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ Phase 3: Tool Registry & Agent RAG Tools                     │
│ └── Create search_standards & get_guidelines_by_domain tools│
│ └── Checkpoint: Test ReAct tool execution & formatting      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ Phase 4: Review Agent Prompt & ReAct Integration             │
│ └── Update review.txt & ReviewAgent for rule citation       │
│ └── Checkpoint: Run review against code with violations     │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ Phase 5: End-to-End Orchestration & Langfuse Observability   │
│ └── Wire into main.py SDLC loop & verify trace inspection   │
│ └── Checkpoint: Full task execution from plan to evaluation │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Phase-by-Phase Breakdown

### 🔹 Phase 1: Knowledge Corpus Creation & Rule Design
**Goal**: Build a structured, modular knowledge repository covering all 6 domains with standardized rule IDs (e.g. `[SEC-INJ-01]`, `[ARCH-SOLID-01]`).

* **Components to Build**:
  * `knowledge_base/coding_standards/clean_code_and_pep8.md`
    * Naming conventions, function length, cyclomatic complexity, typing.
  * `knowledge_base/security_owasp/owasp_top_10.md`
    * SQL/Command injection, hardcoded secrets, broken auth, input sanitization.
  * `knowledge_base/architecture/principles_and_solid.md`
    * SOLID principles, layered architecture, decoupling, circular dependencies.
  * `knowledge_base/api_standards/rest_api_conventions.md`
    * REST resource naming, status codes, standard error payload `{error: {code, message}}`, pagination.
  * `knowledge_base/testing_guidelines/unit_and_integration.md`
    * AAA pattern, mock isolation, edge case coverage, deterministic testing.
  * `knowledge_base/company_standards/company_policies.md`
    * Structured logging (no PII), timeout budgets on I/O, prohibited packages.
* **Verification Checkpoint**:
  * Run a validation script to confirm all markdown files have valid headers, rule IDs, and clean markdown structure.

---

### 🔹 Phase 2: ChromaDB Ingestion & Vector Retrieval Service
**Goal**: Learn how ChromaDB embeds, indexes, and performs metadata-filtered similarity search on custom documentation.

* **Components to Build**:
  * Update `requirements.txt` with `chromadb>=0.5.0` (and `sentence-transformers` for offline embedding fallback).
  * `services/knowledge_service.py`:
    * Markdown chunking with header-aware metadata extraction (`domain`, `rule_id`, `title`, `severity`).
    * ChromaDB collection initialization with persistent local storage in `data/chroma_db/`.
    * OpenAI `text-embedding-3-small` embedding function (with fallback to Chroma's default sentence embedding).
    * Retrieval APIs:
      * `search(query: str, domain: Optional[str] = None, top_k: int = 3)`
      * `get_by_rule_id(rule_id: str)`
* **Verification Checkpoint**:
  * Run `tests/test_knowledge_service.py` to verify:
    1. Documents are chunked and indexed into ChromaDB.
    2. Query `"how to prevent SQL injection"` returns `[SEC-INJ-01]`.
    3. Filtering by `domain="api_standards"` returns REST status code rules.

---

### 🔹 Phase 3: Tool Integration (`rag_tools.py`)
**Goal**: Expose the RAG knowledge service as standard tools that LLM agents can call dynamically.

* **Components to Build**:
  * `plugins/rag_tools.py`:
    * Tool: `rag_tools.search_standards(query: str, domain: str = "")`
    * Tool: `rag_tools.get_guidelines_by_domain(domain: str)`
    * Tool: `rag_tools.get_rule(rule_id: str)`
  * Register in `plugins/tool_registry.py` and `plugins/__init__.py`.
* **Verification Checkpoint**:
  * Run a standalone tool execution test to verify that `ToolExecutor` correctly calls `rag_tools` and returns formatted markdown strings for LLM consumption.

---

### 🔹 Phase 4: Review Agent & Prompt Enhancement
**Goal**: Teach the `ReviewAgent` to use the RAG tools, retrieve relevant rules, and cite explicit rule IDs in its findings.

* **Components to Build**:
  * `prompts/review.txt`:
    * Update instructions to guide the agent:
      1. First analyze code characteristics (e.g. database queries, REST routes, error handling).
      2. Call `rag_tools.search_standards` for relevant domains.
      3. Format review report with rule citations (e.g. `Findings: - [High] [SEC-INJ-01] Raw SQL string formatting used...`).
  * `agents/review_agent.py`:
    * Connect the agent with the tool registry.
    * Support ReAct tool loop for dynamic standard lookup.
* **Verification Checkpoint**:
  * Run a test script providing bad code snippets (hardcoded password, missing error handling, unmocked DB in tests) and verify the agent's review output flags them with exact rule IDs.

---

### 🔹 Phase 5: End-to-End Pipeline & Langfuse Tracing
**Goal**: Integrate the RAG-empowered review agent into the full SDLC pipeline in `main.py` and observe the full trace.

* **Components to Build**:
  * Integrate knowledge initialization into `main.py`.
  * Ensure Langfuse traces capture:
    * Tool call queries to ChromaDB.
    * Retrieved context snippets and similarity scores.
    * Final review verdict and reflection loop behavior.
* **Verification Checkpoint**:
  * Run `python main.py` with a realistic prompt (e.g., "Build a user registration service with input validation and SQLite repository").
  * Verify end-to-end execution where `ReviewAgent` validates the generated project against our RAG knowledge base.

---

## 🎯 How We Will Proceed

We will start with **Phase 1 (Knowledge Corpus Creation & Rule Design)**. Once we write and review the knowledge files, we will move to **Phase 2 (ChromaDB Ingestion)** and test it thoroughly before proceeding!
