# Hospital Agent Loop

## Purpose
This document defines the orchestration loop for the hospital agent.

The design takes the Hermes idea of a platform-agnostic core agent loop, but keeps it much thinner for the hospital project.

## Target Flow

```text
Telegram User
  -> Telegram Bot
  -> Telegram Layer
  -> Agent Loop
  -> Memory/State Check
  -> Backend API Tool
  -> Agent Response Assembly
  -> Telegram Layer
  -> Telegram User
```

## V1 Loop Steps
1. receive Telegram message
2. normalize it into an internal request shape
3. identify whether the message is:
   - FAQ or simple hospital guidance
   - availability request
   - booking request
   - reschedule request
   - cancellation request
   - out-of-scope request
4. load temporary session state
5. load bounded memory if useful
6. decide next action:
   - answer directly
   - ask follow-up
   - call backend API wrapper
   - stop or escalate
7. call existing backend API wrappers only
8. interpret backend response safely
9. update state
10. send patient-friendly response

## Key Design Rule
The agent loop is responsible for orchestration only.

The backend remains responsible for:
- authentication
- authorization
- appointment truth
- availability truth
- business rules
- database operations

## Why This Layer Is Needed
Without an explicit loop layer, the project only has:
- Telegram channel files
- prompt files
- tool files

That is not enough for a real assistant flow.

The loop layer is what connects:
- intent understanding
- follow-up questions
- tool calling
- state updates
- safe stopping conditions

## Hermes Reference Applied Here
Adopted ideas from Hermes:
- separate messaging layer from core agent loop
- separate agent loop from tools
- keep memory as a distinct concern
- keep state/session handling separate from durable memory

Not adopted from Hermes for V1:
- multi-platform support
- plugin provider system
- advanced skill automation
- full session database
- autonomous self-improving learning loop
