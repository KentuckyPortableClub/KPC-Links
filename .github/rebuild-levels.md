# PR rebuild levels (1–5)

Every PR gets a level. A check sets it automatically from the changed files. The owner can override it with a line in the PR body:

    Rebuild-level: N

or a label `rebuild:N`. The body line wins over a label, and a label wins over the auto level.

A full rebuild should almost never happen. It is only the monthly run, or an explicit owner `full_rebuild=yes`. Even a level-5 rule change is a check: existing keys are verified against the new rules (`RULES_VERIFY`). Verify still *builds* every area whose code part moved; a byte-identical output is recorded as verified-same, not “skipped.” Merging a PR does not start a run by itself.

| Level | Plain words | What is rebuilt |
| --- | --- | --- |
| 1 | A minor change: tests, docs, workflows, or a helper that is not a rule file. | Nothing. |
| 2 | Data for named areas (an owner hand file, one country's outlines, taking a country off the expected-holds list). | Only those areas. |
| 3 | A declared rule-scope change that names some areas, not all. | Only the declared areas. |
| 4 | Shared data that can move many area hashes. | Only the areas whose hashes actually moved. |
| 5 | A rule-file change, an undeclared change, or a declared scope of `all`. | Verify existing keys. Every area whose code part moved is built; byte-identical output is verified-same. Not a full rebuild. |

The US, Canada and world key plan jobs honour `REBUILD_LEVEL` when it is set (PR body / label / `GITHUB_ENV`), or they compute the auto level from this checkout versus `origin/main` (Quality #179 M9). Level 1 does not expand an undeclared rules change to every area (the monthly run and an explicit `full_rebuild=yes` still do). Level 5 sets a verify, never `KPC_FULL_BUILD`. Levels 2–4 leave the planned list to the area hashes and the declared scope.

After the PR is merged, a nightly on main has an empty diff versus `origin/main`, so the auto level would be 1. The workflows then leave the list to the recorded hashes and `RULES_VERIFY`. Merging a PR does not start a run by itself.
