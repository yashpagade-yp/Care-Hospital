# Tools

This folder stores backend API wrapper tools used by the hospital agent.

Planned responsibilities:
- doctor list and availability wrapper
- appointment booking wrapper
- appointment reschedule wrapper
- appointment cancellation wrapper
- authentication helper wrapper if needed
- clean outputs for the agent loop to interpret

Rules:
- every real action must call existing backend APIs
- no direct database access
- no business-rule duplication that belongs in the backend
- tools should be called by the agent loop, not by Telegram transport directly
