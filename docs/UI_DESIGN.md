# UI Design Plan — HR Admin Dashboard

The only user-facing surface in scope (see [TASKS.md](../TASKS.md) P4) is the **HR Admin Dashboard**: where recruiters review candidate rankings, see why a score was given, and override decisions. Everything else in the system (ingestion, scoring, integrations) is API-only.

## Goals
- Let an HR reviewer see ranked candidates for a job req at a glance
- Make scores explainable, not a black box (surfaces the P3 explainability data)
- Let a reviewer override/flag a score, feeding the human-in-the-loop requirement
- Nothing fancy — internal tool, optimize for clarity and speed over visual polish

## Screens (in build order)

1. **Job Req List** — table of open reqs, candidate count, screening status
2. **Candidate Ranking View** (core screen) — ranked list for one req: name, score, top matched/missing skills, status (new/reviewed/overridden)
3. **Candidate Detail** — full resume text/parsed fields side-by-side with JD, score breakdown (reason codes / feature attribution from P3), override control + comment field
4. **Audit/History View** — read-only log of past decisions and overrides per candidate (compliance trace, pulls from the audit log in Postgres)

Login/auth screen is needed but trivial — defer styling, just gate access.

## Tech choice
- Server-rendered pages (Jinja2 templates via FastAPI) for v1 — no separate frontend build/deploy, fastest to ship, matches "internal tool" scope
- Revisit a React/Vite SPA only if the dashboard grows interactive features (live filtering, drag-to-reorder, etc.) that make full-page reloads painful
- Component styling: a plain CSS framework (e.g., Pico.css or Tailwind via CDN) — avoid a design system for an internal tool with one audience

## Layout conventions
- Left nav: Job Reqs / (selected req) Candidates / Audit Log
- Score shown as a number + a small bar/chip, never just a raw float
- Overrides always require a reason (free text) — enforced at the form level, not just convention
- Flag anything PII-sensitive (name, school) as visually de-emphasized by default, with a "show identifying info" toggle — supports the fairness/blind-review goal in P3

## Build phases
1. Read-only ranking view wired to the existing scoring API (no auth yet, local only)
2. Add candidate detail + explainability panel
3. Add override workflow + audit log view
4. Add auth/access control before any real deployment

## Explicitly out of scope for v1
- Candidate self-service portal
- Mobile layout
- Real-time updates/websockets — polling is fine at this volume
