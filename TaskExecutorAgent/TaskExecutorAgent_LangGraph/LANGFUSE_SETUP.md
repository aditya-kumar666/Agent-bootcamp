# Langfuse Cloud Observability Integration Guide

This guide explains how to set up Langfuse Cloud for monitoring and observability in TaskExecutorAgent.

## Overview

Langfuse is a free, open-source LLM observability platform that traces LLM calls, tool executions, and agent workflows. It provides:

- ✅ Real-time execution tracing
- ✅ Automatic token counting and cost tracking
- ✅ Beautiful cloud dashboards for monitoring
- ✅ Agent debugging and replay capabilities
- ✅ A/B testing and prompt versioning
- ✅ **FREE tier:** 1M observations/month (no credit card needed)

## Quick Start (5 Minutes)

### Step 1: Sign Up for Langfuse Cloud

1. **Visit:** https://langfuse.com
2. **Click "Get Started"**
3. **Sign up with email** (free tier)
4. **Create organization** (default name is fine)

### Step 2: Get Your API Keys

1. **In Langfuse Dashboard:** Settings → API Keys
2. **Copy:** Public Key (starts with `pk_`)
3. **Copy:** Secret Key (starts with `sk_`)

### Step 3: Configure Your Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit .env file and add your keys:
```

**Edit `.env` and update these lines:**
```env
LANGFUSE_PUBLIC_KEY=pk_your_public_key_from_langfuse
LANGFUSE_SECRET_KEY=sk_your_secret_key_from_langfuse
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Run Your Agent

```bash
python main.py
```

**Traces will automatically appear in Langfuse Cloud dashboard!**

### Step 6: View Your Traces

1. **Open:** https://your-organization.langfuse.com
2. **Go to:** Traces tab
3. **See:** All your agent executions in real-time

---

## Architecture

```
┌─────────────────────────────────────┐
│    TaskExecutorAgent (Python)       │
│  • Planner Agent                    │
│  • Coding Agent                     │
│  • Review Agent                     │
│  • etc.                             │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  Langfuse Python SDK                │
│  (observability/langfuse_client.py) │
└────────────────┬────────────────────┘
                 │
                 ▼
        ┌─────────────────────┐
        │ Langfuse Cloud API  │
        │  (cloud.langfuse.com)
        └──────────┬──────────┘
                   │
    ┌──────────────┴──────────────┐
    │                             │
    ▼                             ▼
Data Storage           Langfuse Dashboard
(Cloud Postgres)       (Web UI)
```

---

## What Gets Logged

### **Agent Executions**
- Agent name and type (Planner, Coder, Reviewer, etc.)
- Input task
- Output response
- Execution time
- Success/failure status

### **LLM Calls**
- Model name (`gpt-4o-mini`)
- Tokens used (prompt + completion)
- **Cost calculated automatically**
- Latency in seconds

### **Tool Calls**
- Tool name and arguments
- Tool execution time
- Success or error messages
- Tool output (truncated for readability)

### **Complete Traces**
```
Task → Planner → Coder → Reviewer → (Reflection if needed) → Evaluator
```
Shows entire workflow with all branching and retry attempts.

---

## Langfuse Cloud Dashboard

### **Real-Time Traces**
```
┌─────────────────────────────────────┐
│  Recent Traces                       │
├─────────────────────────────────────┤
│ ✅ planner_agent    (2.5s, $0.08)  │
│ ✅ coding_agent     (8.3s, $0.42)  │
│ ✅ review_agent     (1.2s, $0.05)  │
│ ✅ evaluation_agent (0.8s, $0.03)  │
└─────────────────────────────────────┘
```

### **Token Usage & Costs**
```
┌─────────────────────────────────────┐
│  Analytics Dashboard                 │
├─────────────────────────────────────┤
│ Total Tokens: 2,450,000             │
│ Prompt: 1,800,000 (70%)             │
│ Completion: 650,000 (30%)           │
│ Estimated Cost: $12.45              │
│ Avg Cost/Run: $0.58                 │
└─────────────────────────────────────┘
```

### **Error Tracking**
```
┌─────────────────────────────────────┐
│  Errors & Issues                     │
├─────────────────────────────────────┤
│ LLM Errors: 2 (0.2%)                │
│ Tool Errors: 3 (0.3%)               │
│ Retries Triggered: 5 (5.1%)         │
│ Success Rate: 98.5%                 │
└─────────────────────────────────────┘
```

---

## Environment Setup

### Required Variables
```bash
OPENAI_API_KEY=sk_your_openai_key_here
LANGFUSE_PUBLIC_KEY=pk_your_langfuse_public_key
LANGFUSE_SECRET_KEY=sk_your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Optional Variables
```bash
VERBOSE_LOGS=true          # More detailed output
ENABLE_REFLECTION=true     # Enable retry on errors
ENABLE_MEMORY=true         # Enable agent memory
```

---

## Example Workflow

### **1. Agent Runs**
```bash
$ python main.py
[OK] Langfuse observability enabled
[OK] Registered 14 tools
Using model: gpt-4o-mini
```

### **2. Real-Time Traces**
```
→ Trace created: TaskExecutorAgent.main
  → Span: planner_agent.plan
    → Generation: llm_call (2500 tokens, $0.08)
  → Span: coding_agent.execute
    → Generation: llm_call (8500 tokens, $0.25)
  → Span: review_agent.review
    → Generation: llm_call (1200 tokens, $0.04)
  → Span: evaluation_agent.evaluate
    → Generation: llm_call (800 tokens, $0.02)
✓ Trace complete: Total cost $0.39
```

### **3. View in Dashboard**
- Open Langfuse → Traces
- Click on trace
- Expand each node
- See all details including tokens and cost

---

## Pricing

### **Free Tier** ✅
- **Cost:** $0
- **Includes:** 1M observations/month
- **Great for:** Development, testing, learning
- **No credit card required**

### **Pro Tier** (Optional)
- **Cost:** $99/month
- **Includes:** Unlimited observations
- **Great for:** Production use

---

## Troubleshooting

### **Issue: "Langfuse initialization failed"**
**Solution:** 
1. Check that credentials are correct in `.env`
2. Verify LANGFUSE_HOST is `https://cloud.langfuse.com`
3. Test credentials at https://langfuse.com/settings/api-keys

### **Issue: No traces showing in dashboard**
**Solution:**
1. Confirm API keys are set in `.env`
2. Restart agent: `python main.py`
3. Wait 5-10 seconds for traces to sync
4. Refresh dashboard

### **Issue: "Invalid credentials"**
**Solution:**
1. Get fresh API keys from Langfuse
2. Copy the EXACT values (including `pk_` and `sk_` prefixes)
3. Update `.env` file
4. Restart agent

### **Issue: Can't access dashboard**
**Solution:**
1. Verify you're at: `https://your-org.langfuse.com`
2. Check you're signed into the correct organization
3. Organization name is shown in Langfuse interface

---

## Integration Code

### **In Agents (automatic)**
```python
from observability import get_langfuse_client

observer = get_langfuse_client()

with observer.trace("agent_execution") as trace:
    # Your code here
    result = self.llm.invoke(messages)
    observer.generation(trace, "llm_call", model, input, output)
```

### **In main.py (automatic)**
```python
from observability import get_langfuse_client

observer = get_langfuse_client()
# ...run agents...
observer.flush()  # Send final traces to Langfuse
```

---

## Advanced Usage

### **Custom Metadata**
```python
with observer.trace("agent_run", metadata={
    "user": "john",
    "project": "beta",
    "version": "v2.1"
}) as trace:
    # Your code
```

### **Filter Traces**
```
Dashboard → Traces → Filter
By: agent="coding_agent", status="error"
Shows: All failed coding attempts
```

### **Export Data**
```
Langfuse → Analytics → Export
Formats: CSV, JSON
Use for: Analysis, reports, audits
```

---

## Cost Estimation

### **Free Tier (1M observations/month)**
```
Average run: ~4,500 tokens
Cost per run: ~$0.05
Monthly budget: Can handle 20,000 runs
```

### **Token Breakdown**
- Prompt tokens: ~70% of total
- Completion tokens: ~30% of total
- OpenAI pricing: ~$0.000015 per prompt token

---

## Next Steps

1. ✅ Sign up at https://langfuse.com
2. ✅ Get API keys from Settings → API Keys
3. ✅ Update `.env` with your credentials
4. ✅ Run: `pip install -r requirements.txt`
5. ✅ Run agent: `python main.py`
6. ✅ View dashboard: `https://your-org.langfuse.com`

---

## Resources

- **Langfuse Website:** https://langfuse.com
- **Documentation:** https://langfuse.com/docs
- **GitHub:** https://github.com/langfuse/langfuse
- **Community:** https://discord.gg/mC7T93hD7V

---

**You're all set! Your agent is now logging to Langfuse Cloud. 🎉**

Traces will appear automatically in your dashboard as you run the agent.
