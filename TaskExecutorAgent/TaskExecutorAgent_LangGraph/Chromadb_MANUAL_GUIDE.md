# Phase 2: Manually Build and Query the Knowledge Base

These steps intentionally keep ingestion separate from the agents so you can observe what is stored and retrieved.

## 1. Install the Phase 2 dependencies

From `D:\Agent\TaskExecutorAgent\TaskExecutorAgent_LangGraph`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The first local query may download Chroma's default embedding model. An internet connection is required for that initial download.

## 2. Add your own Markdown document

Create a file anywhere, for example `D:\Agent\my_guidelines.md`:

```markdown
# My Guidelines

- **Domain:** `my_domain`
- **Tags:** `reliability`, `python`

## Rule [MY-RULE-01] — Use bounded retries

- **Severity:** high
- **Tags:** `retries`, `timeouts`
- **Requirement:** Retry only transient failures and cap attempts with backoff.
- **Rationale:** Unbounded retries amplify outages.
- **Examples:** Retry a timeout twice, then return a safe failure.
```

Every document must have a `Domain` metadata line and one or more `## Rule [RULE-ID] — Title` sections. Each rule should include `Severity`, `Tags`, `Requirement`, `Rationale`, and `Examples`.

## 3. Ingest one document

```powershell
.\.venv\Scripts\python.exe scripts\knowledge_cli.py ingest D:\Agent\my_guidelines.md
```

The default database is `data/chroma_db/`. It is ignored by Git because it is generated state.

## 4. Ingest the Phase 1 corpus manually

```powershell
.\.venv\Scripts\python.exe scripts\knowledge_cli.py ingest knowledge_base
```

This indexes each rule as a separate chunk. Running ingestion again safely upserts the same rule IDs.

## 5. Search semantically

```powershell
.\.venv\Scripts\python.exe scripts\knowledge_cli.py search "how do I prevent SQL injection"
```

Limit results to one domain:

```powershell
.\.venv\Scripts\python.exe scripts\knowledge_cli.py search "which HTTP status means not found" --domain api_standards --top-k 3
```

`distance` is Chroma's distance score; lower generally means more similar for the configured embedding function.

## 6. Retrieve an exact rule

```powershell
.\.venv\Scripts\python.exe scripts\knowledge_cli.py rule SEC-INJ-01
```

## 7. Experiment safely

Use a separate database while learning:

```powershell
.\.venv\Scripts\python.exe scripts\knowledge_cli.py --db data/chroma_experiment ingest D:\Agent\my_guidelines.md
.\.venv\Scripts\python.exe scripts\knowledge_cli.py --db data/chroma_experiment search "bounded retries"
```

To reset an experiment, delete its directory while no Python process is using it. Do not delete the database during an active query.

## What to observe

1. The Markdown rule becomes one Chroma document.
2. `metadata` contains `domain`, `rule_id`, `title`, `severity`, `tags`, and `source`.
3. Domain filtering narrows the candidate rules before similarity ranking.
4. Exact rule lookup uses metadata rather than semantic similarity.