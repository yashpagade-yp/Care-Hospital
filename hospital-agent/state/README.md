# State

This folder represents temporary conversation and workflow state for hospital-agent sessions.

Unlike `memory/`, this state is short-lived and flow-specific.

## Purpose
- track active appointment-booking flow progress
- track pending clarification questions
- track temporary patient verification stage
- track selected doctor or selected appointment during one flow
- track prescription lookup flow progress

## Storage Decision
- SQLite is a good fit for session state in hospital-agent
- use SQLite for temporary and operational assistant-side state
- do not use SQLite here as the source of truth for prescriptions or hospital records

## V1 State Examples
- current intent: booking, reschedule, cancel, faq
- selected doctor id
- requested date or slot candidate
- pending slot hold id
- last asked follow-up question
- verification step in progress
- selected appointment id for prescription lookup

## State Rules
- keep state temporary and minimal
- never treat state as the source of truth
- refresh important truth from backend APIs
- clear expired or completed flow state

## Memory vs State
- `memory/` is bounded durable context
- `state/` is temporary flow coordination
