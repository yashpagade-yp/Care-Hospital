# Hospital Agent Folder Structure

## Purpose
This document defines the intended V1 structure of `my_hospital/hospital-agent`.

The goal is to keep Telegram transport, assistant behavior, backend API wrappers, and documentation separated clearly.

## Structure

```text
hospital-agent/
  README.md
  plan.md
  .env.example
  agent/
    README.md
  memory/
    README.md
    MEMORY.md
    USER.md
  prompts/
    README.md
  state/
    README.md
  tools/
    README.md
  telegram/
    README.md
  docs/
    agent-loop.md
    backend-api-mapping.md
    folder-structure.md
    hermes-fit.md
    memory-and-state.md
```

## Folder Meaning

### `prompts/`
- stores assistant prompts and safety guidance
- keeps conversational behavior separate from runtime code

### `agent/`
- stores the core orchestration loop
- connects Telegram inputs, memory/state, and backend tool calls

### `memory/`
- stores both short-term and long-term assistant memory design
- short-term memory should be SQLite-friendly
- long-term memory must remain compact and non-sensitive

### `state/`
- stores temporary flow coordination design
- tracks in-progress appointment workflows

### `tools/`
- stores backend API wrapper tools
- acts as the bridge from assistant decisions to backend API calls

### `telegram/`
- stores Telegram bot integration logic
- handles message intake and message delivery
- should not hold backend business rules

### `docs/`
- stores architecture and implementation notes
- keeps planning and reference material close to the assistant layer

## V1 Principle
- keep the structure thin
- keep backend as source of truth
- keep Telegram as the communication channel only
- separate durable memory from temporary state
- separate short-term memory from long-term memory
- keep a real agent loop layer instead of mixing logic into Telegram files
