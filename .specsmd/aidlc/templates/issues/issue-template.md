---
id: ISS-{YYYY}-{NNN}
title: "{short, specific issue title}"
type: bug
status: reported
reported_at: "{YYYY-MM-DDTHH:MM:SSZ}"
reporting_path: "{where/how the report was submitted}"
affected_version: "{application version/build, or unknown}"
affected_commit: "{commit SHA, or unknown}"
environment: "{production|staging|development|local|unknown}"
module: "{affected product module or subsystem}"
severity: "{critical|high|medium|low|unassessed}"
reproducibility: "{always|intermittent|once|not-reproduced|unknown}"
related_issues: []
---

# {ISSUE-ID}: {Short issue title}

## Summary

{One or two sentences stating what is broken and who or what is affected.}

## Exact description

{Describe the observed failure precisely. Preserve the reporter's meaning; distinguish reported facts from agent inferences.}

## Where it happened

- **Product path / screen / URL / API:** {exact route, URL, endpoint, or screen}
- **Reporting path:** {how the issue was reported, such as user report, support ticket, or monitoring alert}
- **Affected module:** {module and relevant sub-area}
- **First observed:** {date and time with timezone, or unknown}
- **Frequency:** {how often it occurs}
- **Affected users/data/workflow:** {scope and impact, or unknown}

## Steps to reproduce

1. {Starting state and account/role, using synthetic or redacted data}
2. {Action}
3. {Action that triggers the failure}

## Expected behavior

{What should happen.}

## Actual behavior

{What happened instead, including exact visible error or incorrect result.}

## Environment

- **Application version/build:** {exact affected version}
- **Commit/release identifier:** {SHA or release tag, if known}
- **Environment:** {production, staging, development, local, or unknown}
- **OS/device/browser/client:** {relevant details or not applicable}
- **Relevant configuration:** {non-secret configuration only, or none known}

## Severity and workaround

- **Severity:** {critical|high|medium|low|unassessed, with a short impact-based reason}
- **Workaround:** {safe workaround, or none known}

## Evidence

Store attachments in this issue's `evidence/` directory. List each file and what it demonstrates. Redact secrets, credentials, tokens, and personal data before saving evidence.

| File | Type | Description | Captured at (UTC) |
|------|------|-------------|------------------|
| {filename or none} | {image/log/recording/other} | {what it shows} | {timestamp or unknown} |

## Triage and resolution

- **Owner:** {unassigned or name}
- **Related bolt/task:** {identifier or none}
- **Resolution:** {pending}
- **Resolved in version/commit:** {pending}
- **Verification:** {pending}
- **Closed at:** {pending}

## Reporter notes

{Additional context, constraints, or exact wording that does not fit above. Use `None` if empty.}
