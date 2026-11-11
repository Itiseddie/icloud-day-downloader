"""
pull_day.py - download the photos and videos from one day (or a range of days) from iCloud.

It calls icloudpd, which handles Apple's login and keeps its own saved session.
Read-only: nothing in iCloud is deleted or changed.

Examples (PowerShell):
  python pull_day.py 2026-11-04                 one day
  python pull_day.py 2026-11-04 2026-11-06      a range of days
  python pull_day.py 2026-11-04 --videos-only   skip still photos
  python pull_day.py 2026-11-04 --recent 300    only scan the newest 300 items (fast for recent days)
  python pull_day.py 2026-11-04 --shared        download from your Shared Photo Library (found automatically)
  python pull_day.py 2026-11-04 --library       show a menu of your libraries and pick one
  python pull_day.py --list-libraries           just show your library names
  python pull_day.py 2026-11-04 --library SharedSync-XXXXXXXX   or name a library directly

Files go to:  Downloads\\iCloud <date>\\
"""
import argparse, datetime as dt, json, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config.json"          # remembers your Apple ID (no password is stored)
EXTS = {".jpg", ".jpeg", ".heic", ".png", ".mov", ".mp4", ".m4v", ".gif", ".dng"}


def die(msg):
    print("\n  " + msg + "\n")
    sys.exit(1)


def day_arg(s):
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        die(f"'{s}' isn't a date. Use YYYY-MM-DD, for example 2026-11-04.")


def list_libraries(exe, user):
    """Run icloudpd --list-libraries, show its output live (so any password or 2FA prompt is visible),
    and return (exit code, library names found)."""
    proc = subprocess.Popen(exe + ["--username", user, "--list-libraries"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    chunks = []
    while True:
        b = proc.stdout.read1(1024)
        if not b:
            break
        sys.stdout.write(b.decode(errors="replace"))
        sys.stdout.flush()
        chunks.append(b)
    proc.wait()
    text = b"".join(chunks).decode(errors="replace")
    names = list(dict.fromkeys(re.findall(r"PrimarySync|SharedSync-[A-Za-z0-9-]+", text)))
    return proc.returncode, names


def choose_library(exe, user, shared_only):
    """Look up the libraries and pick one: automatically if there is only one shared library, else a numbered menu."""
    code, names = list_libraries(exe, user)
    if not names:
        die("Couldn't read the library list (see the messages above). Don't retry in a loop: repeated failed logins can lock your Apple Account.")
    if shared_only:
        names = [n for n in names if n.startswith("SharedSync-")]
        if not names:
            die("No Shared Photo Library was found on this account.")
        if len(names) == 1:
            print(f"\n  Using your shared library: {names[0]}")
            return names[0]
    print("\n  Which library?")
    for i, n in enumerate(names, 1):
        print(f"    {i}. {n}  ({'your personal library' if n == 'PrimarySync' else 'shared'})")
    while True:
        choice = input("  Type a number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(names):
            return names[int(choice) - 1]
        print("  Please type one of the numbers above.")


def main():
    p = argparse.ArgumentParser(description="Download one day (or range) of iCloud photos and videos.")
    p.add_argument("start", nargs="?", help="day to download, YYYY-MM-DD")
    p.add_argument("end", nargs="?", help="optional last day, YYYY-MM-DD")
    p.add_argument("--user", help="Apple ID email (remembered after the first time)")
    p.add_argument("--videos-only", action="store_true", help="skip still photos")
    p.add_argument("--out", help="folder to save into (default: Downloads\\iCloud <date>)")
    p.add_argument("--recent", type=int, metavar="N",
                   help="only look at the newest N items, then stop (much faster for recent days)")
    p.add_argument("--library", metavar="NAME", nargs="?", const="ASK",
                   help="library to read: a name like SharedSync-XXXXXXXX, or no name to pick from a menu "
                        "(default: your personal library, PrimarySync). Put the dates before this option.")
    p.add_argument("--shared", action="store_true",
                   help="use your Shared Photo Library (looked up automatically, nothing to copy)")
    p.add_argument("--list-libraries", action="store_true",
                   help="show the libraries on your account (personal and shared) and exit")
    a = p.parse_args()

    if not a.list_libraries:
        if not a.start and a.library and re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.library):
            die(f"'{a.library}' looks like a date. Put the dates first, then the option, for example:\n  python pull_day.py {a.library} --library")
        if not a.start:
            p.error("a start day is required, for example: python pull_day.py 2026-11-04")
        start = day_arg(a.start)
        end = day_arg(a.end) if a.end else start
        if end < start:
            die(f"The end day ({end}) comes before the start day ({start}).")

    # Find icloudpd (the command, or as a Python module).
    exe = [shutil.which("icloudpd")] if shutil.which("icloudpd") else [sys.executable, "-m", "icloudpd"]
    if subprocess.run(exe + ["--version"], capture_output=True).returncode != 0:
        die("icloudpd isn't installed. Run:  python -m pip install icloudpd")

    # Remember the Apple ID (never the password).
    cfg = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
    user = a.user or cfg.get("apple_id") or input("  Apple ID email: ").strip()
    if not user:
        die("An Apple ID is needed.")
    cfg["apple_id"] = user
    CONFIG.write_text(json.dumps(cfg, indent=2))

    if a.list_libraries:
        print("\n  Libraries on this account:\n")
        code, names = list_libraries(exe, user)
        print("\n  PrimarySync is your personal library. A name starting with SharedSync- is the Shared Photo Library.")
        print("  No need to copy a name: use  --shared  or  --library  (with no name) and the script picks for you.")
        sys.exit(code)

    library = a.library
    if library and re.fullmatch(r"\d{4}-\d{2}-\d{2}", library):
        die(f"'{library}' looks like a date. Put the dates first, then the option, for example:\n  python pull_day.py {library} --library")
    if a.shared or library == "ASK":
        library = choose_library(exe, user, shared_only=a.shared)

    label = str(start) if start == end else f"{start} to {end}"
    shared = " - shared library" if library and library != "PrimarySync" else ""
    out = Path(a.out) if a.out else Path.home() / "Downloads" / f"iCloud {label}{shared}"
    out.mkdir(parents=True, exist_ok=True)

    cmd = exe + ["--username", user, "--directory", str(out), "--folder-structure", "none",
                 "--skip-created-before", str(start),
                 "--skip-created-after", f"{end}T23:59:59",
                 "--no-progress-bar"]
    if library:
        cmd += ["--library", library]
    if a.videos_only:
        cmd.append("--skip-photos")
    if a.recent:
        cmd += ["--recent", str(a.recent)]
    elif (dt.date.today() - end).days <= 30:
        print("  Tip: this day is recent. Add  --recent 300  to stop early instead of scanning your whole library.\n")

    free = shutil.disk_usage(out).free / 1e9
    print(f"\n  Downloading {label} from iCloud into:\n  {out}\n  Free space on this drive: {free:,.0f} GB.\n"
          "  First time: you'll type your Apple ID password and approve a 2-factor code on your iPhone.\n"
          "  Your library is checked newest to oldest, so it can take a few minutes.\n"
          "  Nothing is deleted from iCloud. If it stops, run the same command again to resume.\n"
          "  If the login fails, do NOT keep retrying: repeated failures can lock your Apple Account.\n")
    r = subprocess.run(cmd)

    files = [f for f in out.iterdir() if f.is_file() and f.suffix.lower() in EXTS]
    vids = sum(f.suffix.lower() in {".mov", ".mp4", ".m4v"} for f in files)
    mb = sum(f.stat().st_size for f in files) / 1e6
    print(f"\n  {len(files)} files ({vids} videos, {len(files) - vids} photos), {mb / 1000:,.2f} GB, in {out}")
    if r.returncode != 0:
        print("  The downloader reported a problem (see above). Re-running the same command resumes.")


if __name__ == "__main__":
    main()
