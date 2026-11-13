# PR rebuild levels (1–5)

Every PR gets a level. A check sets it automatically from the changed files. The owner can override it with a line in the PR body:

    Rebuild-level: N

or a label `rebuild:N`. The body line wins over a label, and a label wins over the auto level.

A full rebuild should almost never happen. It is only the monthly run, or an explicit owner `full_rebuild=yes`. Even a level-5 rule change is a check: existing keys are verified against the new rules, and only an area whose output actually changes is rebuilt. Merging a PR does not start a run by itself.

| Level | Plain words | What is rebuilt |
| --- | --- | --- |
| 1 | A minor change: tests, docs, workflows, or a helper that is not a rule file. | Nothing. |
| 2 | Data for named areas (an owner hand file, one country's outlines, taking a country off the expected-holds list). | Only those areas. |
| 3 | A declared rule-scope change that names some areas, not all. | Only the declared areas. |
| 4 | Shared data that can move many area hashes. | Only the areas whose hashes actually moved. |
| 5 | A rule-file change, an undeclared change, or a declared scope of `all`. | Verify existing keys. Rebuild only an area whose output actually changes. Not a full rebuild. |

The key workflows honour the level: level 1 does not plan a rebuild (unless it is the monthly run or `full_rebuild=yes`); level 5 sets a verify, not `KPC_FULL_BUILD`.
