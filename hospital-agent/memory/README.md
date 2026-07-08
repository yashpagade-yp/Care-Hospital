# Memory

This folder stores bounded assistant memory for the hospital agent.

This is inspired by Hermes memory concepts, but reduced for hospital-agent V1.

## Purpose
- keep only small, durable, non-sensitive assistant memory
- preserve useful user preferences or workflow notes across conversations
- keep hospital-agent behavior consistent without storing full medical data

## Memory Types

### Short-Term Memory
- used during an active or recent conversation flow
- helps the agent remember what the patient just asked
- helps the agent continue booking, reschedule, cancellation, FAQ, or prescription lookup flows
- should expire or be cleared when no longer useful

### Long-Term Memory
- used for compact durable notes that help across conversations
- stores stable assistant-side notes and safe user preferences
- must remain bounded, minimal, and non-sensitive

## Storage Decision
- use SQLite as the local storage mechanism for assistant-side memory and state if we persist them
- SQLite here belongs to the hospital-agent layer only
- SQLite must not become a second hospital medical-record database

## What Memory Is For
- patient communication preferences if explicitly useful
- safe hospital-assistant operating notes
- stable hospital FAQ guidance notes
- workflow lessons for the assistant layer
- short-term conversation continuity
- long-term assistant consistency

## What Memory Must Not Store
- full patient medical records
- diagnosis notes
- raw OTP values, passwords, or secrets
- anything that bypasses backend authorization
- unnecessary personal health information

## V1 Memory Model
- short-term memory
  - preferably backed by SQLite
  - stores recent conversation and flow continuity
  - closely related to session state
- long-term memory
  - `MEMORY.md`
    - assistant-side durable notes
    - hospital-agent operational facts
  - `USER.md`
    - compact user preference notes only when genuinely helpful

## Boundary With Backend
- patient data authority remains in backend APIs
- memory is supportive context, not source of truth
- appointment truth must always come from backend APIs
- prescription truth must always come from backend APIs
