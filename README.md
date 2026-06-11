
# Python MCP Masterclass

A hands-on course covering the Model Context Protocol (MCP) with Python .
This repo pairs every server with a runnable client, one pattern per folder, so you can see both sides of the protocol.
Coming up: OAuth, updated tasks/elicitation per the new RC.

> The MCP spec just dropped a major release candidate with changes to several patterns (tasks, elicitation, sampling, logging) within the next 10 weeks. `1_intro` is already covered in full on YouTube — that stable core (tools, resources, prompts, structured output, transports, pagination) isn't going anywhere. The priority now is building against the next version of the spec. 
>
> **What's in this repo.** Most modules are adapted from the [official python-sdk examples](https://github.com/modelcontextprotocol/python-sdk/tree/main/examples) and converted into paired `server.py` / `client.py` teaching files — one pattern per folder, easy to run and follow. A handful of modules are still missing (notably OAuth), which will be added in a future update.

---

## Prerequisites

### Knowledge

You should be comfortable with basic Python before starting. The topics below are covered in **Section 0** — skip it if you're already familiar with them:

- Intermediate Python: decorators, JSON handling, type hints
- Async/await
- SQLite3 basics
- Starlette and Uvicorn basics

Section 0 is not a hard stop for everyone. If you're comfortable with these topics, jump straight to `1b_function_calling.ipynb`.

### Software Requirements

- An Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com) → API Keys → Create Key
- Python 3.10 or higher (MCP requires Python >=3.10; this guide uses 3.11)
- Node.js 18 or higher (required for MCP tooling)

---

## Environment Setup

### Windows

**1. Install `uv` (run in PowerShell, then restart your terminal)**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**2. Verify `uv` is installed**

```powershell
uv --version
```

**3. Install Python 3.11**

```powershell
uv python install 3.11
```

**4. Create a virtual environment**

```powershell
uv venv --python 3.11
```

**5. Activate the environment**

```powershell
.venv\Scripts\activate
```

**6. Install required packages**

```powershell
uv pip install "mcp[cli]" ipykernel pillow anthropic uvicorn
```

**7. Verify MCP is installed**

```powershell
python -c "import mcp; print(mcp.__file__)"
```

**8. Install Node.js (LTS) — required for MCP tooling**

```powershell
winget install --id OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
```

If `winget` is not available, download Node.js from [nodejs.org](https://nodejs.org) (minimum version: Node 18).

**9. Verify Node.js**

```powershell
node -v
npm -v
```

---

### macOS

**1. Install `uv`**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal after installation.

**2. Verify `uv` is installed**

```bash
uv --version
```

**3. Install Python 3.11**

```bash
uv python install 3.11
```

**4. Create a virtual environment**

```bash
uv venv --python 3.11
```

**5. Activate the environment**

```bash
source .venv/bin/activate
```

**6. Install required packages**

```bash
uv pip install "mcp[cli]" ipykernel pillow anthropic uvicorn
```

**7. Verify MCP is installed**

```bash
python -c "import mcp; print(mcp.__file__)"
```

**8. Install Node.js (LTS) — required for MCP tooling**

Using Homebrew:

```bash
brew install node@18
```

Or download from [nodejs.org](https://nodejs.org) (minimum version: Node 18).

**9. Verify Node.js**

```bash
node -v
npm -v
```

---

## Set Your API Key

Set the `ANTHROPIC_API_KEY` environment variable before running any code.

**Windows (PowerShell)**

```powershell
$env:ANTHROPIC_API_KEY = "your-key-here"
```

**macOS / Linux**

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

---

> Some sections support HTTP transport in addition to the default STDIO transport. See the comments at the bottom of each `server.py` for instructions.

---

## Course Outline

| Folder | Topic |
|--------|-------|
| `0_prerequisite/` *(optional)* | Intermediate Python, decorators, type hints, async/await, SQLite3, Starlette/Uvicorn |
| `1b_function_calling.ipynb` | Anthropic API tool use and the request/response cycle |
| `1_intro/section_1_simple_tools/` | MCP tools — text, lists, titles, and Field-documented parameters |
| `1_intro/section_2_resources/` | MCP resources — static resources and dynamic URI templates |
| `1_intro/section_3_prompts/` | MCP prompts — string prompts and message-list prompts |
| `1_intro/section_4_structured_returns/` | Structured return types — Pydantic models, TypedDict, and typed dicts |
| `1_intro/section_5_calltoolresult/` | `CallToolResult` patterns — errors, embedded resources, images, and metadata |
| `1_intro/section_6_async_context/` | Async tools, progress reporting, and server-sent notifications |
| `1_intro/section_7_full_tour/` | Full tour combining every concept from Sections 1–6 |
| `2a_lifespan_counter/` | Lifespan management — counter |
| `2b_lifespan_sqlite/` | Lifespan management — SQLite |
| `2c_completion/` | Completions |
| `2d_tool_pagination/` | Tool pagination |
| `2e_sampling/` | Sampling |
| `2f_elicitation/` | Elicitation |
| `3a_path_config/` | Path configuration |
| `3b_starlette_mounting/` | Starlette mounting |
| `4a_lowlevel_basic/` | Low-level server — basic |
| `4b_lowlevel_direct_call_tool/` | Low-level server — direct call tool result |
| `4c_simple_resource_lowlevel/` | Low-level server — simple resource |
| `4d_structured_output_lowlevel/` | Low-level server — structured output |
| `5a_lifespan_counter_lowlevel/` | Low-level lifespan — counter |
| `5b_lifespan_sqlite_lowlevel/` | Low-level lifespan — SQLite |
| `5c_pagination_lowlevel/` | Low-level pagination |
| `6a_lowlevel_sse_transport/` | Low-level SSE transport |
| `6b_lowlevel_sse_polling/` | Low-level SSE polling |
| `7a_lowlevel_simple_task/` | Low-level task — simple |
| `7b_lowlevel_task_interactive/` | Low-level task — interactive |
