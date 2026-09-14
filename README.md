# agentops-triage-kit
[![tests](https://github.com/monicaslgc/agent-triage-kit/actions/workflows/tests.yml/badge.svg)](https://github.com/monicaslgc/agent-triage-kit/actions/workflows/tests.yml)

A small, dependency-free demo of a multi-agent triage and escalation pipeline. Tickets come in, get classified, get checked against known issue patterns, and either get auto-resolved or handed off to a human, with a full audit trail along the way.

This is a portfolio project, not a copy of anything I've built at work. It's original code from scratch, meant to show the shape of a problem I deal with professionally (automating triage/escalation for engineering and support workflows) without pulling in any actual employer or client code.

## Why this pattern

Autonomous "AI agents" are easy to demo and hard to actually trust. In my experience the hard part was never the model call itself, it's the pipeline around it: how confident does an agent need to be before it's allowed to act without a human, what gets logged so you can audit it later, and where do you leave room to swap a rule-based stub for a real model without rewriting the orchestration.

This project is my attempt at a minimal, readable answer to that.

## Architecture

```mermaid
flowchart LR
    T[Ticket] --> TR[TriageAgent]
    TR -->|severity + category| INV[InvestigatorAgent]
    INV -->|diagnosis + confidence| ESC[EscalationAgent]
    ESC -->|confidence >= threshold| AR[Auto-resolved]
    ESC -->|confidence < threshold OR critical| HU[Escalated to human]
```

Three agents run in a fixed pipeline, each with one job:

- **TriageAgent** classifies severity (low/medium/high/critical) and category (auth/integration/infrastructure/data) from the ticket text.
- **InvestigatorAgent** checks the ticket against a small runbook of known issue patterns and proposes a diagnosis plus a next step, with a confidence score attached.
- **EscalationAgent** is the actual policy gate. Critical tickets always go to a human. Everything else only auto-resolves if the investigation's confidence clears a threshold (`MIN_AUTO_RESOLVE_CONFIDENCE`, 0.7 by default).

Every agent appends an `Action` to the ticket's `Report`, so what you get at the end isn't just a verdict, it's a trail of what each step decided and why.

### The LLM seam

Each agent takes an optional `brain: LLMClient | None`. Left as `None` (the default here), agents fall back to plain rules, which is why this whole thing runs offline with no dependencies and is easy to unit test. `agentops/brain.py` defines the `LLMClient` protocol; implement `.complete(prompt) -> str` for whatever provider you're using and pass it to `Orchestrator(brain=...)` to move from rules to real model calls. None of the orchestration logic has to change either way.

## Project layout

```
src/agentops/
  models.py        # Ticket, Action, Report, Severity, Category
  agent.py         # Agent base class
  brain.py         # LLMClient protocol (the rule-based <-> model seam)
  runbook.py       # known-issue knowledge base + matcher
  orchestrator.py  # runs the agent pipeline
  agents/
    triage.py
    investigator.py
    escalation.py
examples/
  tickets.json     # sample synthetic tickets
  run_demo.py      # CLI entry point
tests/
  test_orchestrator.py
  test_runbook.py
```

## Running it

```bash
python examples/run_demo.py
```

```bash
pip install -e ".[dev]"
pytest
```

No API keys, no external services. Everything runs locally.

## Example output

```
Ticket T-1004: Full outage - all services down
  severity=critical category=unknown
  [triage] classified as critical/unknown (confidence=0.40)
  [investigator] no matching known issue found (confidence=0.20)
  [escalation] escalated to human (confidence=1.00)
  -> escalated to human

Ticket T-1003: User can't log in, token expired error
  severity=high category=auth
  [triage] classified as high/auth (confidence=0.90)
  [investigator] Likely an expired or misconfigured auth credential. (confidence=0.80)
  [escalation] auto-resolved (confidence=0.80)
  -> resolved
  recommendation: Verify token/key expiry and rotation schedule for the affected integration.
```

## Extending it

- Add a new `Agent` subclass and drop it into `Orchestrator(agents=[...])`.
- Swap `runbook.match()` for something real, like a vector search over past incidents or a wiki API. The `InvestigatorAgent` interface doesn't need to change.
- Implement `LLMClient` and pass `brain=` to one agent at a time as you move from rules to actual model calls, instead of doing it all at once.

## License

MIT, see [LICENSE](LICENSE).
