# Release grade file: the steps, by hand, AFTER the one build's sample (22 Nov 2026)

Owner's wiring plan, job 5. Steps only: nothing here has been run. NO BUILDING still holds; these steps come after the build,
after the fresh blind sample of 300 is graded, and after you decide per state.

Why: the Release (`kpc-release.yml`, `kpc_release.py grade_allows`) promotes a state only when `data/status/quality/verdicts.json`
is for the SAME KPC-Links commit and build and marks that state `RELEASE-READY: YES`. Nothing has ever written that file, so
today no state can be released. `keeper/release_grades.py` in KPC-Store writes it. It decides nothing: a state is YES only
when your decisions file says yes for that build.

## What you need

1. **The build's commit and build id.** The commit is the full sha on KPC-Links main of the build. The build id is the `build`
   field of `data/us-key/index.json` at that commit.
2. **The graded sample** (private, stays in KPC-Store), for example `key-quality/<date>/.../answers.csv`. It needs the columns
   `area`, `ref` and `is_our_outline_the_park`. If planted rows were used, also the plants list (`--plants rows.json`).
3. **Your decisions file**, one row per state: `area, release, build, decided_by, when, note, no_worse_than_live`.
   - `release` = `yes` or `no`.
   - `build` = the build id above.
   - `decided_by` = `KPC owner`.
   - Any state not listed, or listed for another build, comes out NO. That is the safe way.

## Steps (a chat with the private store attached, or your PC)

1. In a clone of KPC-Store main:
   ```
   python3 keeper/release_grades.py \
       --answers <graded sample .csv> [--plants <rows.json> --pass pass1] \
       --decisions <your decisions .csv> \
       --sha <KPC-Links commit of the build> --build <build id> \
       --out verdicts.json
   ```
   It exits 0 when written, 1 when an input cannot be read (then nothing is written).
2. Read `verdicts.json`. It must hold counts only for each state, no park number or name. If a park shows, stop: the sample
   is private.
3. Put it in KPC-Links as `data/status/quality/verdicts.json` through a pull request, never straight onto main.
   - Branch `prep/<date>-release-grades`, with one commit holding only that file.
   - Commit as `KPC owner <KentuckyPortableClub@users.noreply.github.com>`; the message says the build id and the sample date.
   - You merge it.
4. Release by numbers, state by state: Actions, then "Release map files (by hand)" (`kpc-release.yml`), then Run workflow.
   - `source_sha` = the same full commit as step 1.
   - `areas` = the states you said yes to.
   - `grade` empty (it then reads the file from step 3).
   - A state without YES, or one that would be worse than live, is not released and keeps its live data.

## Check before you press the button

- The release guards (#302: a state outline only in the state whose key lists the park, none by name+pin unless named, Nevada
  US-2635) still hold each state they hold. The grade file does not lift them.
- The sha in `verdicts.json` must match the build. A file made for an older build refuses every state, as it should.
