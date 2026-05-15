# TaskExecutorAgent_LangGraph

Python version of the same multi-agent SDLC flow using LangGraph:
Planner -> Coding -> Review -> (Reflection -> Re-Coding -> Review)* -> Evaluation.

## Setup

```bash
cd TaskExecutorAgent/TaskExecutorAgent_LangGraph
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Put your key in `.env`:

```env
OPENAI_API_KEY=your_key_here
```

## Run

```bash
python main.py
```
