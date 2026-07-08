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
- Telegram access and backend authorization are separate concerns.

## Responsibilities Of Hospital Agent
The hospital agent is responsible for:
- handling Telegram conversations
- handling Telegram bot message flow
- understanding patient requests
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

## Not Allowed In V1
- Diagnosis
- Prescription decisions
- Emergency medical advice
- Full patient record access without verification

## Folder Purpose
This `hospital-agent/` folder contains the assistant-specific work, such as:
- planning
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

## Integration Rules
- The hospital backend remains the source of truth.
- All real business actions must go through backend APIs.
- Telegram should communicate with the hospital agent, not directly with the backend.
- The Telegram bot token is only for Telegram channel communication, not for backend authorization.
- The hospital agent may talk with any Telegram user at the conversation layer, but protected patient actions must respect backend auth and verification.
- The assistant should use only approved tools and flows.

## Current Build Direction
- For now, this hospital-agent work should avoid Docker-specific setup.
- Start with a simple non-Docker Telegram bot integration path.
- Add Docker or deployment-specific packaging only later if actually needed.

## First Implementation Goal
The first end-to-end flow should be:
1. Patient sends appointment request on Telegram
2. Hospital agent understands the request
3. Hospital agent checks doctor availability via backend API
4. Hospital agent books or helps book the appointment
5. Hospital agent sends confirmation on Telegram

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
