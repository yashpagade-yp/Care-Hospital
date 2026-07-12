# Hospital Agent

## Purpose
`hospital-agent` is the assistant integration layer for the `my_hospital` project.

It does not replace the hospital backend or frontend.
It acts as the bridge between:
- Telegram users
- Telegram bot communication
- assistant logic
- existing hospital backend APIs

## Main Architecture
```text
Telegram User -> Telegram Bot -> Hospital Agent -> Hospital Backend APIs -> Response -> Telegram Bot -> Telegram User
```

## Project Context
The main hospital project already has:
- completed frontend
- completed backend
- completed database
- completed business logic
- working APIs

This folder is only for the missing assistant layer and Telegram integration.

## Telegram Communication Model
- Telegram communication starts through a Telegram bot created in BotFather.
- The bot token is the channel credential that allows the hospital agent to receive and send Telegram messages.
- A Telegram user talks to the bot first, not directly to the backend.
- The hospital agent receives the Telegram message, understands the request, and decides whether a backend API call is needed.
- General conversation and hospital FAQ guidance can start from Telegram without immediately performing a protected backend action.
- Protected actions like booking, rescheduling, cancellation, and patient-specific appointment lookup must still follow backend authentication and verification rules.
- Existing prescription viewing is allowed only when the backend confirms the patient is authorized to view it.
- Telegram access and backend authorization are separate concerns.

## Responsibilities Of Hospital Agent
The hospital agent is responsible for:
- handling Telegram conversations
- handling Telegram bot message flow
- understanding patient requests
- responding naturally in English, Hindi, or Marathi
- filtering doctors by specialty or patient need
- calling approved backend APIs
- returning simple and safe responses
- enforcing assistant safety rules
- supporting appointment-related flows

## What Hospital Agent Must Not Do
The hospital agent must not:
- replace backend business logic
- access the database directly unless explicitly designed safely
- bypass backend authentication or authorization
- provide unsafe diagnosis or emergency medical advice
- expose patient data without verification

## V1 Scope
### Users
- Patient

### Features
- Check doctor availability
- Book appointment
- Reschedule appointment
- Cancel appointment
- Answer hospital FAQs
- View existing prescriptions that already exist in backend records

## Not Allowed In V1
- Diagnosis
- Prescription decisions or medicine generation
- Emergency medical advice
- Full patient record access without verification

## Folder Purpose
This `hospital-agent/` folder contains the assistant-specific work, such as:
- planning
- agent loop design
- short-term memory, long-term memory, and temporary state design
- prompts
- Telegram integration
- backend API wrappers
- safety rules
- assistant documentation

Suggested contents:
- `plan.md`
- `.env.example`
- `prompts/`
- `tools/`
- `telegram/`
- `docs/`

Current structure:
- `README.md`
- `plan.md`
- `.env.example`
- `main.py`
- `config.py`
- `requirements.txt`
- `agent/`
- `memory/`
- `prompts/`
- `state/`
- `tools/`
- `telegram/`
- `docs/`

## Integration Rules
- The hospital backend remains the source of truth.
- All real business actions must go through backend APIs.
- Telegram should communicate with the hospital agent, not directly with the backend.
- The Telegram bot token is only for Telegram channel communication, not for backend authorization.
- The hospital agent may talk with any Telegram user at the conversation layer, but protected patient actions must respect backend auth and verification.
- SQLite may be used in hospital-agent for assistant-side memory and state, but not as a replacement for hospital backend records.
- The assistant should use only approved tools and flows.

## Current Build Direction
- For now, this hospital-agent work should avoid Docker-specific setup.
- Start with a simple non-Docker Telegram bot integration path.
- Add Docker or deployment-specific packaging only later if actually needed.
- Keep a separate agent-loop layer so orchestration does not get buried inside Telegram files.
- Keep both short-term and long-term memory concepts in the assistant layer.
- Keep durable memory bounded and safe.
- Keep temporary state separate from memory.

## First Implementation Goal
The first end-to-end flow should be:
1. Patient sends appointment request on Telegram
2. Hospital agent understands the request
3. Hospital agent checks doctor availability via backend API
4. Hospital agent books or helps book the appointment
5. Hospital agent sends confirmation on Telegram

## Current Implementation Status
- Telegram bot entry code exists
- backend API client code exists
- SQLite-backed session and short-term memory code exists
- agent loop code exists for:
  - login + OTP verify
  - doctor listing
  - availability lookup
  - appointment listing
  - booking flow
  - cancellation flow
  - reschedule flow
  - prescription listing and lookup
  - FAQ fallback
  - multilingual English, Hindi, and Marathi responses
  - specialty-based doctor search with filtered booking continuity

## Run Locally
1. Create `hospital-agent/.env`
2. Add the Telegram bot token and backend base URL
3. Install dependencies from `hospital-agent/requirements.txt`
4. Run `python hospital-agent/main.py`

## Development Workflow
Follow the hospital project Git workflow:
- Start from an issue when work should be tracked
- Create a feature branch from `development`
- Push changes to the feature branch
- Open PR to `development`
- Never push directly to `main`
- `development` to `main` must go through PR and owner approval

## Notes
Hermes and OpenClaw are kept outside the hospital project as reference/framework repos.
They should not be copied into this folder as product code.
