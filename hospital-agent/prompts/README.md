# Prompts

This folder stores assistant prompt assets for the hospital agent.

Planned prompt files:
- system prompt for hospital assistant behavior
- safety prompt for out-of-scope requests
- FAQ guidance prompt
- appointment booking flow prompt
- appointment reschedule and cancellation prompt
- memory-aware response guidance for the agent loop

Rules:
- keep prompts patient-friendly and short
- do not embed backend business logic here
- do not allow diagnosis, prescription, or unsafe emergency advice
- prompts support the agent loop, but do not replace orchestration or state handling
