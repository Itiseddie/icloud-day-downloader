# iCloud Day Downloader (pull_day.py)

Downloads the photos and videos from one day (or a range of days) in your iCloud library to a folder on your Windows laptop.

- It runs **icloudpd**, a free downloader that handles Apple's login and keeps its own saved session.
- **Read-only.** It never deletes or changes anything in iCloud.
- Safe to re-run. Files already downloaded are skipped, so an interrupted run resumes.

> **Unofficial tool, use at your own risk.** This project is not made by or affiliated with Apple. It relies on icloudpd, which uses an unofficial route into iCloud that Apple can change at any time. Repeated failed logins can lock your Apple Account, so never retry a failing login in a loop. You are responsible for your own account and data.

## Which method do I use?

| Your situation | Use |
|---|---|
| Photos are in **your own** iCloud library (taken on your phone, not shared) | `pull_day.py` ([ways 1–7](#ways-to-use-it)) |
| Photos are in your **Shared Photo Library** (shared with your spouse or family) | `pull_day.py` with `--shared` ([way 8](#8-shared-photo-library-spouse-or-family)) |
| Not sure | Run `pull_day.py` first. If it finds **0 files** but you can see the photos on iCloud.com, they are almost certainly in the Shared Library. Go to way 8. |

---

## One-time setup

1. Put `pull_day.py` in any folder, for example `Documents\Pull Day`.
2. On your iPhone: **Settings > your name > iCloud > iCloud.com > Allow Data Access = ON**.
   Older iOS: "Access iCloud Data on the Web" = ON.
3. **Advanced Data Protection must be OFF.** Otherwise Apple blocks this kind of access.
4. Install icloudpd (requires Python 3):
   ```
   python -m pip install icloudpd
   ```

---

## Ways to use it

Run these in PowerShell from the folder that holds `pull_day.py`.

### 1. One day, photos and videos

```
python pull_day.py 2026-11-04
```
Saves to `Downloads\iCloud 2026-11-04\`.

### 2. A range of days

```
python pull_day.py 2026-11-04 2026-11-06
```
Saves to `Downloads\iCloud 2026-11-04 to 2026-11-06\`. Both dates are included.

### 3. Videos only (skip still photos)

```
python pull_day.py 2026-11-04 --videos-only
```
Good when you only want clips, or want to save disk space.

### 4. Save to a different folder

```
python pull_day.py 2026-11-04 --out "D:\Videos\Nov 4"
```
Use this instead of the default Downloads location.

### 5. Choose the Apple ID on the command line

```
python pull_day.py 2026-11-04 --user you@icloud.com
```
Normally you only type it the first time. It's then remembered in `config.json`.

### 6. Fast mode for recent days (`--recent`)

```
python pull_day.py 2026-11-04 --recent 300
```
Without this, icloudpd checks your **entire library**, newest to oldest, skipping everything outside your dates. That can take a very long time. `--recent 300` reads only the newest 300 items and then stops.

- Best for days within the last few weeks.
- If the file count looks short, raise it (`--recent 600`) and run again. Files already downloaded are skipped.
- Don't use it for older dates. The day may be further back than N items.
- If the day is within 30 days and you leave `--recent` off, the script prints a reminder.

### 7. Combine options

```
python pull_day.py 2026-11-04 2026-11-06 --videos-only --recent 500 --out "D:\Videos\Nov trip"
```

### 8. Shared Photo Library (spouse or family)

**Why this exists:** by default the script reads only your *personal* library. If your phone saves photos to a Shared Photo Library, iCloud.com shows them, but a normal run reports "0 files" even though the photos are visible on iCloud.com.

**Easiest: let the script find it for you.** There is nothing to copy or paste.
```
python pull_day.py 2026-11-04 --shared --recent 300
```
It looks up your Shared Library automatically and downloads from it. Files go to `Downloads\iCloud 2026-11-04 - shared library\`, so they stay separate from your personal pull.

**Or pick from a menu.** Use `--library` with no name:
```
python pull_day.py 2026-11-04 --library
```
It lists your libraries (`PrimarySync` is personal, `SharedSync-…` is shared), and you type a number.

**Just want to see the names?**
```
python pull_day.py --list-libraries
```

**Already know the name?** You can still pass it directly: `--library SharedSync-XXXXXXXX`.

Notes:
- Put the dates **before** `--library`. Typing a date right after it makes the script think the date is a library name (it will warn you).
- **To get both libraries for the same day**, run it twice: once as normal and once with `--shared`. Add the same `--out` folder to both if you want everything in one place. Files already there are skipped.
- **How to tell which library a photo is in:** on iCloud.com, open the photo. Shared Library photos have a small two-person badge, and the Library menu at the top filters Personal vs Shared.

---

## Options at a glance

| Option | What it does | Default |
|---|---|---|
| `start` | First day to download, `YYYY-MM-DD` | required (not needed with `--list-libraries`) |
| `end` | Last day to download | same as `start` |
| `--videos-only` | Skip still photos | photos and videos |
| `--out FOLDER` | Where to save the files | `Downloads\iCloud <date>` |
| `--user EMAIL` | Apple ID email (lets you skip `config.json`) | remembered from last time |
| `--recent N` | Only scan the newest N items, then stop | scans the whole library |
| `--shared` | Use your Shared Photo Library, found automatically | off |
| `--library [NAME]` | Pick a library: give a name like `SharedSync-XXXXXXXX`, or no name to choose from a menu | your personal library (`PrimarySync`) |
| `--list-libraries` | Just show the library names on your account, then exit | off |

---

## What happens when you run it

1. Checks icloudpd is installed.
2. Asks for your Apple ID the first time and remembers it in a small `config.json` file that the script creates for you (**the password is never stored**).
3. Creates the output folder and shows the free disk space.
4. Runs icloudpd, which logs in and checks your library newest to oldest. First time only, you enter your Apple password and the 6-digit code from your iPhone.
5. Prints a summary: file count, videos vs photos, and total size.

All files go into one folder (no dated subfolders).

---

## Troubleshooting

| Problem | What to do |
|---|---|
| `icloudpd isn't installed` | Run `python -m pip install icloudpd`. |
| **Account locked** | Stop running it. Unlock at iforgot.apple.com or account.apple.com. Repeated failed logins cause the lock, so never retry in a loop. |
| Login fails or says access is blocked | Check the iPhone setting in step 2 and that Advanced Data Protection is off. |
| Asks for the 2FA code again | The saved session expired (usually every couple of months). Enter the code again. |
| **Zero files, but photos are visible on iCloud.com** | They are most likely in the **Shared Photo Library**. See [way 8](#8-shared-photo-library-spouse-or-family). Also check that photos have finished uploading from the iPhone (Settings > Photos > iCloud Photos). |
| Zero files downloaded (nothing on iCloud.com either) | Check the date format (`YYYY-MM-DD`) and that the day has items. Photos taken late at night can fall on the next day in iCloud's clock, so try a range one day wider. |
| Output shows a gap in dates (for example Nov 1 then Nov 6) | The missing days are in another library or haven't uploaded. A gap in the photo numbers (IMG_0564 to IMG_0619 missing) is a good sign of this. |
| Runs forever, many "skipping" lines | It's scanning your whole library. Press Ctrl+C (downloaded files are kept) and re-run with `--recent 300`. |
| `--recent` not recognized | Your icloudpd version may differ. Run `python -m icloudpd --help` to check. |
| Stops partway | Run the same command again. It resumes and skips what it already has. |
| Not enough disk space | Use `--videos-only` or `--out` to a drive with more room. |

---

## Files in this folder

- `pull_day.py`: the script. This is the only file you need.
- `README.md`: this file.
- `config.json`: **automatic and optional.** You don't create it. The script makes it on first run and it holds only your Apple ID email. Delete it any time and the script just asks again. Don't share it if you pass this folder to someone else.
