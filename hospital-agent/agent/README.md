# Agent

This folder defines the hospital-agent orchestration layer.

It is the missing layer between:
- Telegram message intake
- backend API wrapper tools
- patient-safe assistant responses

## Purpose
- receive a normalized patient request from the Telegram layer
- identify the user intent
- decide the next safe action
- call backend API wrapper tools when needed
- read or update temporary session state
- read bounded memory when useful
- return a simple patient-friendly response

## V1 Agent Loop
1. receive Telegram event from `telegram/`
2. normalize message into a hospital-agent request
3. load session state from `state/`
4. load bounded memory from `memory/`
5. identify intent
6. decide:
   - answer directly
   - ask follow-up question
   - call backend tool
   - stop or escalate
7. call backend API wrapper from `tools/` if needed
8. update temporary state
9. return response to Telegram layer

## Important Boundaries
- this folder must not replace backend business logic
- this folder must not directly access the database
- diagnosis and emergency advice remain out of scope
- patient-specific actions must respect backend auth and verification

## Planned Contents
- agent loop implementation
- intent routing
- follow-up question handling
- safety decision checks
- response assembly
