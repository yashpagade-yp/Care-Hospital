# Hospital Agent

## Purpose
`hospital-agent` is the assistant integration layer for the `my_hospital` project.

It does not replace the hospital backend or frontend.
It acts as the bridge between:
- Telegram users
- assistant logic
- existing hospital backend APIs

## Main Architecture
```text
Telegram User -> Hospital Agent -> Hospital Backend APIs -> Response -> Telegram
```

## Project Context
The main hospital project already has:
- completed frontend
- completed backend
- completed database
- completed business logic
- working APIs

This folder is only for the missing assistant layer and Telegram integration.

## Responsibilities Of Hospital Agent
The hospital agent is responsible for:
- handling Telegram conversations
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
- The assistant should use only approved tools and flows.

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
