# Telegram

This folder stores Telegram integration logic for the hospital agent.

Planned responsibilities:
- Telegram bot entry point
- message parsing and routing
- Telegram-to-agent request handling
- agent-to-Telegram response formatting
- Telegram bot command handling if added later
- handoff into the core agent loop

Current direction:
- use a simple bot-token-based integration
- avoid Docker-specific setup for now
- keep Telegram transport separate from backend authorization
- do not let Telegram contain agent-business orchestration directly
