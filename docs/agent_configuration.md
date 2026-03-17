# Agent Configuration Guide

This document covers how to configure the AI agent that drives the Open
Evolutions mutation loop.

---

## Anthropic API Key

The evolution loop requires an Anthropic API key. The agent calls the Anthropic
Messages API to propose Lean 4 code mutations.

### Setting your key

Export the key as an environment variable before running `oe-cli start`:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

To persist the key across shell sessions, add the export line to your shell
profile (`~/.bashrc`, `~/.zshrc`, or equivalent).

### Verifying your key

You can verify the key is set and valid by running a quick test:

```bash
python -c "import anthropic; c = anthropic.Anthropic(); print('OK')"
```

If you see `OK`, the key is configured correctly. If you see an
`AuthenticationError`, double-check that the key is correct and has not expired.

### Cost considerations

Each mutation cycle makes one API call to the configured model (currently
`claude-sonnet-4-20250514`). A typical 10-cycle session will consume roughly
10 API calls. Monitor your usage at
[https://console.anthropic.com/](https://console.anthropic.com/).

---

## Configuring the Evolution Loop

The `oe-cli start` command accepts several flags that control how the agent
operates:

### Cycle count (`--cycles`)

The number of mutation cycles to run in a single session. Each cycle consists of
one LLM call, one Lean compilation, and one result recording step.

```bash
oe-cli start --challenge RZCS --cycles 20
```

Default: 10 cycles.

More cycles give the agent more opportunities to iterate on failed attempts, but
each cycle consumes one API call and one compilation round.

### Time per cycle (`--cycle-minutes`)

The maximum time allowed for a single cycle, in minutes. If a cycle exceeds this
limit, the CLI will log a warning but will not forcefully terminate the
compilation (Lean compilations can be slow).

```bash
oe-cli start --challenge RZCS --cycle-minutes 3
```

Default: 5 minutes per cycle.

### Lineage selection (`--lineage`)

Specify which lineage the agent should focus on. The agent will load that
lineage's `lineage_learnings.json` for approach-specific heuristics and dead
ends.

```bash
oe-cli start --challenge RZCS --lineage operator-theory
```

If omitted, the agent loads all available lineage data and selects its own
strategy.

---

## Docker Sandbox Setup

Running mutations in a Docker container is optional but recommended. It prevents
untrusted Lean code from accessing your host filesystem or network.

### Prerequisites

Install Docker from [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)
and ensure the Docker daemon is running.

### Pulling the Lean 4 image

The sandbox uses the official Lean 4 Docker image:

```bash
docker pull ghcr.io/leanprover/lean4:latest
```

### Running with Docker

Pass the `--docker` flag to `oe-cli start`:

```bash
oe-cli start --challenge RZCS --docker
```

When Docker mode is active, each mutation is compiled inside a container with the
following restrictions:

- **No network access** (`--network=none`) -- the container cannot reach the
  internet.
- **Memory limit** (`--memory=4g`) -- prevents runaway allocations.
- **CPU limit** (`--cpus=2`) -- prevents monopolizing the host.
- **Read-only workspace** -- the mutation file is mounted read-only.

### Running without Docker

If Docker is not available, mutations are compiled locally using `lake env lean`.
This is faster but provides no isolation. The `oe-cli init` command will warn you
if Docker is not detected.

---

## Using Different LLM Providers

The current implementation uses the Anthropic Python SDK and targets
`claude-sonnet-4-20250514`. The agent code lives in `oe_cli/evolve.py` in the
`call_agent` function.

To use a different model or provider:

1. Open `oe_cli/evolve.py`.
2. Locate the `call_agent` function.
3. Replace the `anthropic.Anthropic()` client and `client.messages.create()` call
   with your preferred provider's SDK.
4. Ensure the replacement function returns a string containing a Lean 4 code
   block enclosed in triple-backtick markers.

The rest of the pipeline (prompt construction, execution, logging) is
provider-agnostic. As long as the agent returns valid Lean 4 code, any LLM
backend will work.

A plugin system for provider abstraction is planned for a future release.

---

## Troubleshooting

### "ANTHROPIC_API_KEY not set or invalid"

The `ANTHROPIC_API_KEY` environment variable is missing or contains an invalid
key. Re-export it:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### "Lean 4 / Lake toolchain not found"

The `lean` or `lake` commands are not on your PATH. Install Lean 4 using
[elan](https://github.com/leanprover/elan):

```bash
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh
```

Then restart your shell or run `source ~/.elan/env`.

### "Build timed out after 600 seconds"

Lean compilations can be slow, especially when importing large Mathlib modules.
Ensure you have run `lake update` and `lake build` at least once to populate the
build cache. Subsequent compilations will be significantly faster.

### "Docker not found" warning during init

This is non-fatal. You can still run the evolution loop without Docker; mutations
will compile locally. Install Docker if you want sandboxed execution.

### "No contribution_log.json found" on submit

You need to run at least one evolution session (`oe-cli start`) before
submitting. The contribution log is created automatically during the first cycle.

### "Contains sorry at: line N"

Your Lean code includes a `sorry` placeholder, which is not allowed in
submissions. The agent should produce complete proofs. If this occurs frequently,
try running more cycles to give the agent additional iterations to close proof
gaps.

### Mathlib fetch is extremely slow

The first `lake update` downloads and builds Mathlib, which can take 10-30
minutes depending on your hardware and network connection. This is a one-time
cost. Subsequent updates are incremental.

### Agent returns no code

The LLM response did not contain a recognizable Lean 4 code block. This
sometimes happens if the prompt is too long or the model context window is
exceeded. Try reducing the cycle count or clearing stale session data.
