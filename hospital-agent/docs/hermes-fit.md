# Hermes Fit For Hospital Agent

## Purpose
This document records which Hermes ideas fit `my_hospital/hospital-agent` and which do not.

## Good Fit
- separate Telegram gateway logic from the core assistant loop
- use a thin orchestration layer between Telegram and backend APIs
- keep tool calling separate from prompt files
- keep bounded memory separate from temporary session state
- keep the source of truth outside the assistant layer

## Partial Fit
- Hermes persistent memory model is useful as inspiration, but hospital-agent must store much less
- Hermes session routing is useful as inspiration, but hospital-agent only needs Telegram in V1
- Hermes agent loop pattern is useful, but hospital-agent does not need the full provider/tool/plugin complexity now

## Not A Fit For V1
- autonomous self-improving loop
- multi-platform gateway architecture
- plugin memory providers
- broad tool ecosystem
- large general-purpose session storage model

## Decision
For `my_hospital`, use Hermes as a design reference only.

Adopt:
- channel separation
- orchestration loop separation
- memory and state separation

Do not copy:
- full repo structure
- broad plugin system
- unrelated platform features
