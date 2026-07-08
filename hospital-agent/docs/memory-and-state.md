# Hospital Agent Memory And State

## Purpose
This document defines how memory and temporary state should work inside `hospital-agent`.

The design is inspired by Hermes, but reduced to match hospital safety needs and V1 scope.

## Core Concepts

### Memory
Memory should be split into short-term and long-term layers.

### Short-Term Memory
Short-term memory is recent conversational continuity.

Use short-term memory for:
- what the patient just asked
- the most recent follow-up answer
- recent intent and flow continuity
- near-term context needed across a few turns

Short-term memory should:
- be lightweight
- expire naturally
- work closely with session state
- be a good fit for SQLite-backed local persistence

### Long-Term Memory
Long-term memory is durable and bounded.

Use long-term memory for:
- assistant-side workflow notes
- stable communication preferences
- compact FAQ handling guidance

Do not use either memory layer for:
- patient medical records
- backend source-of-truth data
- sensitive credentials

### State
State is temporary and flow-specific.

Use state for:
- in-progress booking flow
- selected doctor
- pending slot hold
- current verification stage
- last follow-up question

Do not use state as long-term storage.

## Recommended V1 Rule
- backend = source of truth
- state = current flow helper
- short-term memory = recent conversation helper
- long-term memory = small durable context helper

## SQLite Decision
- use SQLite in `hospital-agent` for short-term memory and temporary session state
- SQLite is suitable here because the agent needs lightweight local persistence
- SQLite must not store hospital truth that already belongs to backend systems

Use SQLite for:
- Telegram conversation session state
- short-term memory across recent Telegram turns
- in-progress appointment flow state
- optionally storing compact memory references
- optional lightweight audit or flow traces later

Do not use SQLite for:
- authoritative prescription records
- authoritative appointment records
- full patient medical history
- anything that bypasses backend auth and ownership checks

## Suggested Lifecycle

### Booking Flow
1. patient asks to book appointment
2. short-term memory keeps recent booking context
3. state tracks selected doctor and requested slot
4. backend creates slot hold
5. state tracks temporary hold id
6. backend confirms appointment
7. state is cleared after completion

### Long-Term Preference Example
1. patient consistently prefers short responses
2. the agent may keep a compact long-term note
3. future Telegram replies stay concise
4. no medical truth is stored there

### FAQ Flow
1. patient asks a hospital question
2. agent answers using prompt guidance and local docs
3. short-term memory may keep recent FAQ context
4. long-term memory is only updated if a durable preference becomes useful

### Prescription Retrieval Flow
1. patient asks for an old prescription on Telegram
2. agent identifies prescription lookup intent
3. short-term memory keeps the active prescription request context
4. SQLite-backed session state tracks the lookup flow only
5. backend auth and ownership checks still happen through backend APIs
6. agent fetches the prescription from backend if the patient is allowed
7. agent presents the prescription summary back to the patient

Important rule:
- the prescription itself comes from backend APIs, not from SQLite memory/state

## Hermes Reference Applied Here
Adopted ideas:
- short-term and long-term memory separation
- durable memory should stay bounded
- session state should stay separate from memory
- memory should support the agent, not replace real system records

Hospital-specific safety tightening:
- no patient-record memory store in V1
- no medical reasoning memory
- no auth bypass through saved context
