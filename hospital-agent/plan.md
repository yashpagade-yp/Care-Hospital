# Hospital Agent Plan

## Goal
Build a thin assistant layer inside `my_hospital/hospital-agent` that allows a patient to use Telegram to perform approved appointment-related tasks through existing backend APIs.

## Core Principle
- `backend/` remains the source of truth
- `frontend/` remains the hospital web app
- `hospital-agent/` remains the assistant orchestration layer
- Telegram talks to the hospital agent
- Hospital agent talks to backend APIs
- Backend remains responsible for auth, business rules, and database operations

## V1 Users
- Patient

## V1 Features
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

## Safety Rules
- Never provide final medical diagnosis
- Never provide unsafe emergency advice
- Never expose sensitive patient data without verification
- Never bypass backend auth or business rules
- Stop or escalate when a request is outside allowed scope

## Initial Folder Plan
- `README.md`
- `plan.md`
- `.env.example`
- `prompts/`
- `tools/`
- `telegram/`
- `docs/`

## Implementation Sequence
1. Finalize hospital-agent purpose, scope, and safety boundaries
2. Map the backend APIs needed for V1 appointment flows
3. Define the hospital-agent folder structure
4. Add Telegram integration entry point
5. Add backend API wrapper tools
6. Test one thin end-to-end vertical slice

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
2. Hospital agent identifies booking intent
3. Hospital agent asks follow-up questions if required
4. Hospital agent checks doctor availability through backend API
5. Hospital agent books appointment through backend API
6. Hospital agent sends confirmation back on Telegram

## Expected Assistant Behavior
- Keep responses simple and patient-friendly
- Ask follow-up questions only when needed
- Use approved backend APIs only
- Stay role-aware and scope-aware
- Escalate or stop for risky requests

## Reference Guidance
- Use Hermes and OpenClaw only for ideas and patterns
- Do not copy full Hermes/OpenClaw repos into `my_hospital/`
- Keep all real assistant implementation inside `my_hospital/hospital-agent/`
