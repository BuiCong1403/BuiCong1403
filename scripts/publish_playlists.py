"""Publish generated files; never force-push or guess conflict winners."""
import argparse
from pathlib import Path
import subprocess
import sys
import time
import re


def git(*args, check=True):
    return subprocess.run(["git", *args], check=check, capture_output=True, text=True, encoding="utf-8")


def playlist_content(text):
    # Keep the last content-change time when only the generated header changed.
    return "\n".join(line for line in text.splitlines()
                     if not re.match(r"^#\s*Updated\s*:", line, re.I))


def validate_staged_playlists():
    paths = git("diff", "--cached", "--name-only", "-z").stdout.split("\0")
    unchanged = []
    for name in filter(None, paths):
        if Path(name).suffix.lower() != ".m3u" or not Path(name).exists():
            continue
        before = git("show", f"HEAD:{name}", check=False)
        if before.returncode or not before.stdout.lstrip("\ufeff\r\n ").startswith("#EXTM3U"):
            continue
        after = Path(name).read_text(encoding="utf-8-sig")
        if not after.lstrip().startswith("#EXTM3U") or (
                "#EXTINF" in before.stdout and "#EXTINF" not in after):
            git("restore", "--staged", "--", *filter(None, paths))
            raise RuntimeError(f"Refusing empty/invalid playlist {name}; previous remote output preserved")
        if playlist_content(before.stdout) == playlist_content(after):
            unchanged.append(name)
    for name in unchanged:
        git("restore", "--source=HEAD", "--staged", "--worktree", "--", name)
        print(f"Unchanged channel data: {name}; retaining previous update time.")


def publish(message, paths):
    for state in ("rebase-merge", "rebase-apply", "MERGE_HEAD"):
        if Path(git("rev-parse", "--git-path", state).stdout.strip()).exists():
            raise RuntimeError("Repository already has an unfinished merge/rebase")
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "github-actions[bot]@users.noreply.github.com")
    if git("diff", "--cached", "--name-only").stdout.strip():
        raise RuntimeError("Unexpected staged changes; refusing to publish")
    git("add", "--", *paths)
    validate_staged_playlists()
    changed = git("diff", "--cached", "--quiet", check=False)
    if changed.returncode == 0:
        print("No generated changes.")
        return
    if changed.returncode != 1:
        raise RuntimeError(changed.stderr)
    # Do not rebase with unstaged tracked files, even when they are not published.
    if git("diff", "--name-only").stdout.strip():
        raise RuntimeError("Unstaged tracked changes remain; check workflow file list")
    git("commit", "-m", message)
    Path("publish-failed.patch").write_text(git("format-patch", "-1", "--stdout").stdout, encoding="utf-8")
    for attempt in range(3):
        result = git("push", "origin", "HEAD:main", check=False)
        if result.returncode == 0:
            Path("publish-failed.patch").unlink(missing_ok=True)
            print("Published generated files.")
            return
        print(result.stderr, file=sys.stderr)
        git("fetch", "origin", "+refs/heads/main:refs/remotes/origin/main")
        for _ in range(3):
            if git("merge-base", "HEAD", "origin/main", check=False).returncode == 0:
                break
            if git("rev-parse", "--is-shallow-repository").stdout.strip() != "true":
                raise RuntimeError("No common history with main")
            git("fetch", "--deepen=100", "origin", "main")
        else:
            raise RuntimeError("Common history not found after bounded deepening")
        result = git("-c", "core.editor=true", "rebase", "origin/main", check=False)
        if result.returncode:
            git("rebase", "--abort")
            raise RuntimeError("Rebase failed and was aborted. Download the failed-publication artifact.\n" + result.stderr)
        time.sleep(attempt + 1)
    raise RuntimeError("Push failed after three attempts; generated commit is preserved")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", required=True)
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()
    try:
        publish(args.message, args.paths)
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"::error::{exc}", file=sys.stderr)
        sys.exit(1)
