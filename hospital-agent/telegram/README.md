# Telegram

This folder stores Telegram integration logic for the hospital agent.

Current responsibilities:
- Telegram bot entry point
- message parsing and routing
- Telegram-to-agent request handling
- agent-to-Telegram response formatting
- Telegram bot command handling
- handoff into the core agent loop

Current direction:
- use a simple bot-token-based integration
- avoid Docker-specific setup for now
- keep Telegram transport separate from backend authorization
- do not let Telegram contain agent-business orchestration directly

Current file:
- `bot_app.py`
  - Telegram polling bot
  - command handlers
  - message handlers
  - safe error handling around agent and backend calls
