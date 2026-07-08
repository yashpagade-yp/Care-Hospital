# Tools

This folder stores backend API wrapper tools used by the hospital agent.

Current responsibilities:
- doctor list and availability wrapper
- appointment booking wrapper
- appointment reschedule wrapper
- appointment cancellation wrapper
- authentication helper wrapper
- prescription wrapper
- clean outputs for the agent loop to interpret

Current file:
- `backend_api.py`
  - async backend API client for the hospital assistant layer

Rules:
- every real action must call existing backend APIs
- no direct database access
- no business-rule duplication that belongs in the backend
- tools should be called by the agent loop, not by Telegram transport directly
