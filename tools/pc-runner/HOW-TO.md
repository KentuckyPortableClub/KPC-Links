# KPC 2-fer PC runner - how to use it

Written for a phone. Everything here happens on your own PC. Nothing is
uploaded.

## What this is

The 2-fer bot that runs on GitHub, run here instead, reading the outline
store on this PC. It is **the same code**, not a second copy of the rules:

* the 2-fer rules (`kpc_fers.py`, `kpc_fers_store.py` and the rest) come
  from a download of **KPC-Links at one pinned commit**. `1-GET-CODE.bat`
  makes that download and `0-CHECK-SETUP.bat` refuses to go on if the
  folder is not at exactly that commit.
* the KPC-Data helper scripts (the answer-key gate, the memory guard, the
  POTA pair reader, pick, annotate, the waiting room) are **in this zip**,
  taken from one pinned KPC-Data commit, and every file is checked by its
  sha256 before a run.
* the KPC-Store parts (the bot wrapper, the run plan, the push check) are
  in this zip the same way.

Every run prints the two commits and the rules hashes it used.

## Step by step

### 1. Once: get the code

Double-click **1-GET-CODE.bat**. It needs the internet and Git for Windows
(https://git-scm.com/download/win). It makes two folders beside this file:

* `repos\KPC-Links` - the 2-fer code and the answer keys, at the pinned commit
* `repos\KPC-Data-data` - the data folder the bot reads and writes (`data\`
  only, no code)

The first download takes a few minutes. After that it only updates.

### 2. Check the setup

Double-click **0-CHECK-SETUP.bat**. It prints:

* the pinned commits and whether the download matches them
* the rules hashes (the 2-fer one should be `ef4eef2b2364`)
* how many areas your stores hold
* where the results and the private folder will go

If a path is wrong, open **settings.json** in Notepad and fix it. The two
store folders are the ones the store tools write:

* US and Canada: `...\1-STORE-TOOL\kpc-outline-store-full\results\store`
* world: `...\kpc-outline-store-world\results\store`

### 3. Run the US and Canada 2-fers

Double-click **2-RUN-2FERS.bat**. It asks two questions:

* how many minutes in total (press Enter for 350)
* which areas (press Enter for every area)

Then it works through the areas one at a time, exactly as the GitHub job
does: the answer-key gate, the POTA activation history, passes 1, 2, 3 and
5, the missing check, then the save steps into the KPC-Data folder.

It **stops when the time runs out** and says so. Run it again to carry on
with the areas it did not reach.

If anything is refused for licence reasons the run stops at once with exit
89 and says nothing may be used. That is the guard working.

### 4. Check it and read the summary

Double-click **4-CHECK-AND-SUMMARY.bat**. It writes:

* `RESULTS\to-kpc-data\` - exactly the files a GitHub run would push
* `RESULTS\push-check.txt` - the club's own push check over those files
* `RESULTS\SUMMARY.txt` - areas done, rows, new / gone / same, how many
  rows are marked "partial boundary", and the minutes used

**Never worse** is in the summary: every pair today's live files show must
still be shown. If any pair is missing, the summary says so in capitals and
the run should not be used.

Nothing is uploaded. When the numbers look right, a person (or Claude,
on your word) takes `RESULTS\to-kpc-data\` to a KPC-Data prep branch.

### 5. The world, when you want it

Double-click **3-RUN-WORLD-2FERS.bat**. Same bot, your world store.

**World 2-fers are club room only.** Every file this step writes goes into
the `PRIVATE` folder and must never be uploaded, put in a repo or passed
on. On GitHub the world areas stay switched **off**; this step switches
them on for this PC only (`KPC_FERS_WORLD_STORE=on`, which GitHub ignores).

## The two folders this tool makes

* `RESULTS\` - what you may look at and hand on (after the summary says it
  is clean)
* `PRIVATE\` - the bot's own logs, the withheld lists, the world results
  and `not-shown\` (the pairs the bot stopped looking at, and why, plus
  the missing check's own list of pairs it looked at and did not show:
  both name two parks beside a reason, so neither goes into a published
  file - the pushed files keep the counts). **Club room only.** Never put
  it in a repo.

## IMPORTANT: move the pin after the pull requests are merged

The pinned KPC-Links commit in **pins.json** is today's
`prep/partial-view` branch head, because the partial-boundary change is not
merged yet. `0-CHECK-SETUP.bat` prints a loud warning while the pin is not
part of `main`.

Once KPC-Links pull request 211 and KPC-Store pull request 12 are merged:

1. open **pins.json** in Notepad
2. change `kpc_links_commit` to the commit of KPC-Links `main`
3. run **1-GET-CODE.bat** again, then **0-CHECK-SETUP.bat**

The warning then turns into "on main: yes".

## What it will not do

* it never uploads, pushes or posts anything
* the 2-fer run makes no internet request at all
* it never writes into your store folders: it only reads them
* it never moves a POTA pin
