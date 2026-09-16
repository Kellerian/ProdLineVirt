---
name: review-code-review
description: >-
  Review code changes with the code-review subagent for quality and
  reliability. Use when the user asks for code review, quality review,
  /review-code-review, or проверку качества и надёжности кода.
disable-model-invocation: true
---
# Review Code Review

Use this skill when the user asks to run `/review-code-review` or requests a quality/reliability code review.

Launch exactly one `code-review` subagent with:

- `readonly: true`
- `run_in_background: false` unless explicitly asked to run in background
- `description: "Code Review"`
- `subagent_type: "code-review"`

The subagent gathers the diff itself from the repository. Do not compute the diff before launching it. Use the active workspace or repository root as `Full Repository Path`.

By default, review **branch changes** against the repository's default base branch (e.g. `main`). Only specify a different base branch when the user or PR context requires it.

If the user asks to review a specific PR or branch, check out that branch first (same rules as `/review-bugbot`: confirm before stashing if checkout is blocked).

Use this prompt shape:

```text
Full Repository Path: <absolute repository path>
Diff: <one of: "branch changes", "uncommitted changes", "specific files">
Base Branch: <only when reviewing branch changes against a known non-default base>
Files: <only when Diff is "specific files"; comma-separated paths>
Custom Instructions: <only when the user gave specific review instructions>
```

- Default `Diff`: `branch changes` (merge-base with default branch, including committed, staged, and unstaged).
- `uncommitted changes` — only dirty working tree / index.
- `specific files` — when the user names explicit paths; list them under `Files`.

If the subagent fails:

- Fix incorrect invocation (missing path, wrong prompt shape) and retry once.
- For other failures, retry once with the same prompt.
- If it still fails, report the blocker briefly; do not keep retrying.

After the subagent finishes:

- Empty diff → one sentence: nothing to review.
- No issues → one line, e.g. `Code review found no issues`.
- With findings → compact markdown table: **Severity**, **Location** (`file:line`), **Finding**, sorted by severity (highest first).

Do not fix findings or rerun review unless the user explicitly asks.
