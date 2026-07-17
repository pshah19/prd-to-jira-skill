---
name: prd-to-jira
description: Convert a PRD (Markdown/text) into a structured backlog of Jira-ready epics and tasks, with cross-team dependencies mapped and story points estimated. Use when the user gives you a PRD, spec, or feature brief and asks you to break it into tickets, plan the backlog, estimate the work, or map dependencies for a Jira import.
---

# PRD → Jira Epics & Tasks

Turn a PRD into a backlog: epics, stories/tasks under each epic, dependencies between
work items, and a story-point estimate for every item. Produce one machine-readable
`epics.json` file, then render the human-facing artifacts (Jira CSV, dependency
diagram, backlog doc) from it deterministically.

Do the extraction and estimation yourself, as the model — that is the point of this
skill. Only use `scripts/render_outputs.py` for the mechanical last step of turning
`epics.json` into CSV/Mermaid/Markdown. Never hand-write those derived formats.

## When to use this skill

- The user shares a PRD/spec/brief and asks for epics, stories, tickets, a backlog,
  a project plan, or "break this down."
- The user asks to estimate story points or map dependencies for existing PRD content.
- Do **not** use this for status reporting, sprint metrics, or dependency analysis of
  an *existing* ticket list that has no source PRD — those are separate tools.

## Step 1 — Read the whole PRD first

Read the entire document before extracting anything. Note:
- The distinct feature areas / user-facing capabilities (these become epic candidates).
- Any explicit ordering language ("phase 1", "after X ships", "requires the new API").
- Which systems/teams are implied per area (frontend, backend, mobile, data, infra,
  platform, 3rd-party integration) — this drives both dependencies and labels.
- Explicit non-goals or out-of-scope sections — do not generate tickets for these.

## Step 2 — Extract epics

An epic is a cohesive, shippable slice of the PRD's scope — typically one per major
feature area or user journey, not one per PRD section header. A good PRD of 3-6 pages
usually yields **3-6 epics**. If you find yourself writing more than ~8, look for
epics that are really the same capability split by accident.

For each epic capture: `id` (`EPIC-<n>`), `summary` (imperative, <10 words),
`description` (2-4 sentences: what it delivers and why, pulled from the PRD's intent —
don't just restate the section title), `priority` (High/Medium/Low, inferred from the
PRD's own language — "must have"/"P0" → High, "nice to have"/"stretch" → Low, default
Medium).

## Step 3 — Break each epic into tasks

Under each epic, write stories/tasks small enough to estimate confidently (see
rubric below — nothing should default to "I'll just call it an 8 because I'm unsure").
Aim for **3-8 tasks per epic**. For each task capture:

- `id` (`EPIC-<n>-<m>`)
- `type`: `Story` (user-facing behavior), `Task` (engineering/infra work with no
  direct user-facing behavior), or `Spike` (research/design work needed before the
  real implementation can be estimated — use this instead of guessing on a 13).
- `summary` — imperative, specific enough to be a Jira ticket title on its own.
- `description` — what "done" looks like, in a sentence or two.
- `acceptance_criteria` — 2-5 bullet points, testable.
- `labels` — lowercase, kebab-case, system/team-oriented (e.g. `backend`, `mobile`,
  `payments-api`, `infra`). These are what a later dependency/critical-path tool will
  group by, so be consistent within a document.
- `risk`: `low` / `medium` / `high` — see Step 5.
- `story_points` — see Step 5.
- `depends_on` — see Step 4.

## Step 4 — Map dependencies

For every task, list the `id`s of other tasks that must complete first, as
`depends_on`. Look for:

1. **Sequential build order** — a frontend/consumer task depends on the backend/API
   task it calls; a migration-consuming task depends on the migration task.
2. **Shared foundations** — if two or more tasks need the same schema change, new
   service, or shared component, they all depend on the task that creates it (create
   that shared piece as its own task rather than duplicating it).
3. **Explicit PRD ordering** — "phase 2 requires phase 1", "gated behind the new
   auth flow", etc.
4. **Cross-team handoffs** — a task owned by one team (per its labels) that consumes
   output from a task owned by a different team is a dependency worth flagging even
   if the PRD doesn't say so explicitly, because it's the kind of risk a TPM tracks.

Only record *direct* dependencies (don't list a transitive dependency that's already
implied by the chain — the critical-path tool downstream will compute the transitive
closure). A task with no prerequisites gets `"depends_on": []`.

## Step 5 — Estimate story points and risk

Use Fibonacci points. Judge scope + uncertainty together, not effort alone:

| Points | Scope | Uncertainty |
|---|---|---|
| 1 | Single component/file, no design decisions | None — mechanical change |
| 2 | One system, well-understood pattern | Low — matches existing precedent in the PRD |
| 3 | One system, a few edge cases or states to handle | Low-medium |
| 5 | Touches 2 systems, or one system with real design decisions | Medium |
| 8 | Multiple systems/services, or an external/3rd-party dependency | Medium-high |
| 13 | Spans many systems and/or the PRD is vague about how it should work | High |

If a task would be a 13, prefer splitting it into a `Spike` (to resolve the unknown)
plus a smaller follow-on `Story`/`Task` instead — flag this explicitly in the task's
`description` ("split from a 13 — see spike EPIC-n-m"). Set `risk` to `high` for any
task that depends on an external team/vendor, touches shared infrastructure, or is
based on an ambiguous part of the PRD; `medium` for cross-system tasks; `low`
otherwise.

## Step 6 — Write epics.json

Emit **one JSON file** matching this schema (this is the contract `render_outputs.py`
expects — do not deviate from field names):

```json
{
  "product": "<short product/feature name from the PRD title>",
  "source_prd": "<filename you read>",
  "epics": [
    {
      "id": "EPIC-1",
      "summary": "...",
      "description": "...",
      "priority": "High",
      "tasks": [
        {
          "id": "EPIC-1-1",
          "type": "Story",
          "summary": "...",
          "description": "...",
          "acceptance_criteria": ["...", "..."],
          "labels": ["backend"],
          "risk": "medium",
          "story_points": 5,
          "depends_on": []
        }
      ]
    }
  ]
}
```

## Step 7 — Render outputs

Run the render script once `epics.json` is written and validated (every `depends_on`
id must resolve to a real task id — check this yourself before running the script,
since the script does not validate it):

```bash
python3 skill/scripts/render_outputs.py path/to/epics.json --outdir path/to/output
```

This produces, in `--outdir`:
- `jira_import.csv` — Jira CSV-import-ready (Issue Type, Summary, Description, Epic
  Name, Story Points, Priority, Labels, Acceptance Criteria). Jira's CSV importer
  cannot create issue links on first import (ticket keys don't exist yet), so
  dependencies are **not** in this file — see `dependencies.md` for the manual
  linking step.
- `dependencies.mmd` — a Mermaid `graph TD` of every task and its `depends_on` edges,
  grouped into subgraphs by epic.
- `dependencies.md` — a human-readable dependency list per task, plus the exact
  post-import steps for linking issues in Jira using the generated ids as a
  cross-reference (map `EPIC-1-1` → real Jira key after import, then link).
- `backlog.md` — the full backlog as a readable Markdown doc (epics → tasks →
  acceptance criteria → points), useful for a PRD review meeting even before anyone
  touches Jira.

## Step 8 — Summarize for the user

After rendering, tell the user: epic count, task count, total story points, and any
tasks you flagged as high-risk or split from a 13. Point them at `backlog.md` first
and `jira_import.csv` for the actual import.
