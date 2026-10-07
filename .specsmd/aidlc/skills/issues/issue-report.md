# Skill: Report an Issue

## Role

Capture a reproducible, traceable bug report in the project memory bank. This skill records and organizes the report; it does not implement a fix or convert a feature request into a defect.

## Trigger

Use when a user or agent reports an observed defect, regression, failure, or incorrect result. The Master Agent routes these requests to the Issue Agent.

## Storage and identifiers

- One issue is one folder: `memory-bank/issues/{issue-id}/`.
- Use `ISS-{YYYY}-{NNN}` (for example, `ISS-2026-001`). The sequence restarts each calendar year.
- Before assigning an ID, inspect the existing issue folders and choose the next unused number for the current year. If a proposed folder already exists, do not overwrite it; select another unused ID.
- Each folder contains `issue.md` and `evidence/`. Put screenshots, logs, recordings, and other supporting material in that issue's `evidence/` directory. Create `evidence/README.md` from `.specsmd/aidlc/templates/issues/evidence-README-template.md` so the directory is tracked even before attachments are added.
- Use `.specsmd/aidlc/templates/issues/issue-template.md` as the source template.

## Required report fields

Capture these fields. If the reporter cannot provide a value, write `unknown` or `not provided`; do not guess.

- Unique issue ID and concise title.
- Reporting path: the channel or route through which the issue was submitted, and the product path/screen/URL/API where it occurred.
- Affected application version/build and, when available, commit or release identifier.
- Affected environment and module/subsystem.
- Exact description of the observed behavior, separating reporter-provided facts from any agent inference.
- Steps to reproduce, expected behavior, actual behavior, reproducibility/frequency, and user/workflow impact.
- Severity with a brief impact-based reason, or `unassessed` if impact is unclear.
- Relevant environment details, evidence inventory, and any safe workaround.
- Report timestamp in UTC, lifecycle status, and related issues/bolt/task when known.

## Process

1. Read the root `AGENTS.md` and the applicable issue template. Do not edit application code as part of reporting.
2. Determine whether the report is an observed defect. If it is a feature request or unclear request, route it through the Master Agent to the appropriate AI-DLC flow instead of labeling it a bug.
3. Search existing issue folders for a likely duplicate. If one exists, add its ID to the report or update the existing issue only when the user clearly refers to that same defect; otherwise create a separate report and cross-link it.
4. Collect missing facts needed to make the issue actionable. Ask concise follow-up questions for critical unknowns; never fabricate a version, route, module, reproduction step, or evidence. Mark remaining unknowns explicitly.
5. Allocate the next unused `ISS-{YYYY}-{NNN}` identifier and create the issue folder with `issue.md` and `evidence/README.md`, copying the issue and evidence README templates.
6. Fill the template. Preserve exact error text and relevant reporter wording. Keep the summary concise and the description specific.
7. Add only evidence supplied or explicitly captured for this report. Record each file in the evidence table. Before saving, redact credentials, access tokens, secrets, and unnecessary personal or financial data. Never place secrets in issue text or attachments.
8. Review that the required fields are present or explicitly marked unknown, links and paths are correct, and every attachment belongs to this issue folder.
9. Report the issue ID, saved path, any missing information, and evidence filenames. Do not claim the defect is verified, fixed, or closed unless evidence supports that state.

## Lifecycle

Use `reported` when first recorded. Triage may set an owner and severity; implementation may set `in-progress`; after a fix use `resolved` until verification; set `closed` only after verification. Use `duplicate` or `won't-fix` only with a linked issue or documented rationale. Preserve the report and evidence; do not delete issue folders when status changes.

## Test contract

```yaml
input: User or agent report of an observed defect, plus any supplied context/evidence
output: memory-bank/issues/{issue-id}/issue.md and an evidence directory
required: ID, reporting path, affected version, module, exact description, reproduction details, expected/actual behavior, impact, evidence inventory
```
