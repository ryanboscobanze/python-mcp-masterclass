# Python MCP Masterclass

A hands-on course for learning the **Model Context Protocol (MCP)** with Python. You will build MCP servers and clients from scratch, starting with the Anthropic API fundamentals and progressing through all major MCP concepts.

---

## Prerequisites

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
uv pip install "mcp[cli]" ipykernel pillow anthropic
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
uv pip install "mcp[cli]" ipykernel pillow anthropic
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

## Course Structure

```
python-mcp-masterclass/
├── function_calling.ipynb          # Anthropic API function calling fundamentals
└── 1_intro/
    ├── section_1_simple_tools/     # Tools with primitive return types
    ├── section_2_resources/        # Static and dynamic MCP resources
    ├── section_3_prompts/          # MCP prompt templates
    ├── section_4_structured_returns/  # Pydantic, TypedDict, and typed return types
    ├── section_5_calltoolresult/   # CallToolResult patterns (errors, images, resources)
    ├── section_6_async_context/    # Async tools, progress, and notifications
    └── section_7_full_tour/        # All concepts combined in one server
```

Each section contains a `server.py` (the MCP server) and a `client.py` (the MCP client that connects to it).

---

## Running a Section

Each section's server and client are run separately.

**Terminal 1 — start the server**

```bash
cd 1_intro/section_1_simple_tools
python server.py
```

**Terminal 2 — run the client**

```bash
cd 1_intro/section_1_simple_tools
python client.py
```

> Some sections support HTTP transport in addition to the default STDIO transport. See the comments at the bottom of each `server.py` for instructions.

---

## What You Will Learn

| Section | Topic |
|---------|-------|
| `function_calling.ipynb` | Anthropic API tool use and the request/response cycle |
| Section 1 | MCP tools — text, lists, titles, and Field-documented parameters |
| Section 2 | MCP resources — static resources and dynamic URI templates |
| Section 3 | MCP prompts — string prompts and message-list prompts |
| Section 4 | Structured return types — Pydantic models, TypedDict, and typed dicts |
| Section 5 | `CallToolResult` patterns — errors, embedded resources, images, and metadata |
| Section 6 | Async tools, progress reporting, and server-sent notifications |
| Section 7 | Full tour combining every concept from sections 1–6 |
