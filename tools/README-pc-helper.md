# KPC PC helper: the downloads a bot may not make

Some map layers can't be read by a bot. Their server says no (robots.txt or a 403), or the server is on the "saved copies only"
list (every `services*.arcgis.com` host and `apps.fs.usda.gov`). A person can still download them in a normal browser. This
helper walks you through them one at a time, checks each file, and sends it to the bots.

It never contacts an agency server itself. Your browser opens the page and you click Download. The helper only reads the list
from GitHub and, if you are logged in, uploads with `gh`. Nothing secret is stored in it.

## Once: get ready (about 5 minutes)

1. Install **Python 3** from https://www.python.org/downloads/ . On the first screen tick **"Add python.exe to PATH"**.
2. Get the KPC-Links folder on your PC. Either:
   - with Git: `git clone https://github.com/KentuckyPortableClub/KPC-Links`, or
   - on GitHub: **Code → Download ZIP**, then unzip it (for example to `Documents\KPC-Links`).
3. Optional, for one-click upload: install the **GitHub CLI** from https://cli.github.com/ , then run `gh auth login` once and
   follow its steps. If you skip this, the helper makes ONE upload file for you to send to the bot instead.

## Every time: one command

Open **Command Prompt** (Start → type `cmd`), go to the folder, and run the helper:

```
cd Documents\KPC-Links
python tools\kpc_pc_helper.py
```

Then:

1. It prints the list: each area, layer, and server, plus how many records the saved copy already has.
2. For each one it says **why** it is needed and asks you to press **Enter**. Your browser opens the layer's official page.
3. On that page, find the layer. Choose **Download** (or **Export**), pick **GeoJSON** (or JSON), with **all records and no
   filter**. Save it to your **Downloads** folder as usual. A `.zip` with GeoJSON inside is fine too. A Shapefile is not, so
   pick GeoJSON.
4. When the download has **finished**, go back to the Command Prompt and press **Enter**. The helper then:
   - finds the new file in Downloads,
   - counts the records in that state,
   - checks the count against what the saved copy already has (a smaller download is refused, so nothing is lost),
   - trims the shapes with the same tool the bots use,
   - writes a small checked file `hand-US-XX.<layer>.geojson.gz` in your `kpc-hand` folder.
5. If it says **SHORT** or **could not read**, type `y` and try the download again (all records, no filter), or `n` to move on.
6. Type `s` to skip a layer or `q` to stop. You can run the helper again any time, and it shows only what is still open.
7. At the end it uploads the checked files to the `boundary-cache` release, if `gh` is logged in. Otherwise it packs
   **`kpc-hand-upload.zip`** in your `kpc-hand` folder. Send that one file to the bot in chat and it uploads it.

The next US key run (the master step) checks each file again, merges it into the saved copy (it never makes the copy smaller),
and marks the row done.

## Handy options

- `python tools\kpc_pc_helper.py --list` only shows the list.
- `python tools\kpc_pc_helper.py --only US-AZ` does only Arizona (or `--only "US-AZ|fsod"` for one layer).
- `python tools\kpc_pc_helper.py --downloads D:\MyDownloads` sets your Downloads folder if it was not found.
- `--no-upload` keeps the checked files on your PC and uploads nothing.

## Rows it never opens

A row marked **never** (for example `ncnhde.natureserve.org`, or the Grant County NM parcel server) is skipped. Nobody
contacts those servers, by bot or by hand.

## Only what changed

The helper lists a layer only when it is **new**, was **never downloaded**, or its official source **looks changed**.
Each run of the US key checks the official download pages it is allowed to check (a quick look at the file size and date,
or the catalog's stated date; never a blocked server). When one changed, that layer shows up here again.

Some pages a bot may not check. Those are on a short reminder list. About every 3 months, run:

    python tools\kpc_pc_helper.py --reminders

It only prints the pages. If one shows a newer date or a different record count, tell the bot which one.
