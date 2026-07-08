# Hospital Agent Plan

## Goal
Build a thin assistant layer inside `my_hospital/hospital-agent` that allows a patient to use Telegram to perform approved appointment-related tasks through existing backend APIs.

## Core Principle
- `backend/` remains the source of truth
- `frontend/` remains the hospital web app
- `hospital-agent/` remains the assistant orchestration layer
- Telegram users talk to a Telegram bot
- the Telegram bot talks to the hospital agent
- Hospital agent talks to backend APIs
- Backend remains responsible for auth, business rules, and database operations

## Telegram Layer Decision
- V1 should use a Telegram bot created through BotFather
- the bot token is the Telegram communication credential
- Telegram communication and backend authorization are separate layers
- any Telegram user may start a conversation with the bot at the chat layer
- protected actions must still satisfy backend authentication and patient verification rules
- start with a simple non-Docker Telegram integration path

## SQLite Decision
- use SQLite in hospital-agent for bounded memory and temporary session state
- do not use SQLite as the source of truth for prescriptions, appointments, or medical records
- prescription lookup must come from existing backend APIs only

## V1 Users
- Patient

## V1 Features
- Check doctor availability
- Book appointment
- Reschedule appointment
- Cancel appointment
- Answer hospital FAQs
- View existing prescriptions already present in backend records

## Not Allowed In V1
- Diagnosis
- Prescription decisions or medicine generation
- Emergency medical advice
- Full patient record access without verification

## Safety Rules
- Never provide final medical diagnosis
- Never provide unsafe emergency advice
- Never expose sensitive patient data without verification
- Never bypass backend auth or business rules
- Never generate or alter prescription decisions in the assistant layer
- Stop or escalate when a request is outside allowed scope

## Memory Model Decision
- short-term memory should exist for recent conversational continuity
- long-term memory should exist for bounded durable assistant context
- SQLite should support short-term memory and temporary state
- long-term memory must stay compact and safe

## Initial Folder Plan
- `README.md`
- `plan.md`
- `.env.example`
- `agent/`
- `memory/`
- `prompts/`
- `state/`
- `tools/`
- `telegram/`
- `docs/`

## Folder Structure Status
- `README.md` created
- `plan.md` created
- `.env.example` created
- `agent/` created
- `memory/` created
- `prompts/` created
- `state/` created
- `tools/` created
- `telegram/` created
- `docs/` created

## Implementation Sequence
1. Finalize hospital-agent purpose, scope, and safety boundaries
2. Map the backend APIs needed for V1 appointment flows
3. Define Telegram communication boundaries and patient-safe action rules
4. Define the hospital-agent folder structure
5. Define the core agent loop, bounded memory, and temporary state model
6. Add Telegram integration entry point
7. Add backend API wrapper tools
8. Test one thin end-to-end vertical slice

## Backend APIs Needed First
- doctor availability API
- appointment booking API
- appointment reschedule API
- appointment cancellation API

## Preserved Initial Notes
These points are carried forward from `hospital-agent_plan.md` because they define the first backend integration focus for V1:

### V1 Users
- Patient

### V1 Features
- Check doctor availability
- Book appointment
- Reschedule appointment
- Cancel appointment
- Answer hospital FAQs

### Not Allowed In V1
- Diagnosis
- Prescription decisions
- Emergency medical advice
- Full patient record access without verification

### Backend APIs Needed First
- Availability API
- Appointment booking API
- Appointment reschedule API
- Appointment cancel API

## First Vertical Slice
1. Patient sends appointment request on Telegram
2. Telegram bot passes the message to the hospital agent
3. Hospital agent identifies booking intent
4. Hospital agent asks follow-up questions if required
5. Hospital agent checks doctor availability through backend API
6. Hospital agent books appointment through backend API
7. Hospital agent sends confirmation back through Telegram

## Expected Assistant Behavior
- Keep responses simple and patient-friendly
- Ask follow-up questions only when needed
- Use approved backend APIs only
- Stay role-aware and scope-aware
- Escalate or stop for risky requests
- allow simple hospital conversation without bypassing protected backend actions
- use temporary state for in-progress flows
- use short-term memory for recent flow continuity
- use long-term memory for safe durable context

## Reference Guidance
- Use Hermes and OpenClaw only for ideas and patterns
- Do not copy full Hermes/OpenClaw repos into `my_hospital/`
- Keep all real assistant implementation inside `my_hospital/hospital-agent/`
