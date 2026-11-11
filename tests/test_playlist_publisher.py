import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("publisher", ROOT / "scripts/publish_playlists.py")
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class PublisherTests(unittest.TestCase):
    def run_git(self, directory, *args):
        return subprocess.run(["git", "-C", str(directory), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.remote = self.root / "remote.git"
        self.run_git(self.root, "init", "--bare", "--initial-branch=main", str(self.remote))
        self.work = self.root / "work"
        self.run_git(self.root, "clone", str(self.remote), str(self.work))
        self.run_git(self.work, "config", "user.name", "Test")
        self.run_git(self.work, "config", "user.email", "test@example.com")
        (self.work / "all.m3u").write_text("old\n")
        self.run_git(self.work, "add", ".")
        self.run_git(self.work, "commit", "-m", "initial")
        self.run_git(self.work, "push", "origin", "main")
        self.other = self.root / "other"
        self.run_git(self.root, "clone", str(self.remote), str(self.other))
        self.run_git(self.other, "config", "user.name", "Other")
        self.run_git(self.other, "config", "user.email", "other@example.com")
        old = Path.cwd()
        os.chdir(self.work)
        self.addCleanup(os.chdir, old)

    def remote_change(self, name):
        (self.other / name).write_text("remote change\n")
        self.run_git(self.other, "add", name)
        self.run_git(self.other, "commit", "-m", "concurrent change")
        self.run_git(self.other, "push", "origin", "main")

    def test_success_and_no_change(self):
        Path("all.m3u").write_text("fresh\n")
        publisher.publish("refresh", ["all.m3u"])
        head = self.run_git(self.work, "rev-parse", "HEAD")
        publisher.publish("refresh", ["all.m3u"])
        self.assertEqual(head, self.run_git(self.remote, "rev-parse", "main"))
        self.assertFalse(Path("publish-failed.patch").exists())

    def test_nonconflicting_concurrent_push(self):
        self.remote_change("other.txt")
        Path("all.m3u").write_text("fresh\n")
        publisher.publish("refresh", ["all.m3u"])
        self.assertEqual(Path("other.txt").read_text(), "remote change\n")
        self.assertEqual(self.run_git(self.remote, "show", "main:all.m3u"), "fresh")

    def test_conflict_aborts_without_overwriting_remote(self):
        self.remote_change("all.m3u")
        Path("all.m3u").write_text("fresh local\n")
        with self.assertRaisesRegex(RuntimeError, "aborted"):
            publisher.publish("refresh", ["all.m3u"])
        self.assertEqual(self.run_git(self.remote, "show", "main:all.m3u"), "remote change")
        self.assertEqual(Path("all.m3u").read_text(), "fresh local\n")
        self.assertFalse(Path(".git/rebase-merge").exists())
        self.assertTrue(Path("publish-failed.patch").exists())

    def test_unlisted_edit_is_not_silently_committed(self):
        self.remote_change("other.txt")
        self.run_git(self.work, "pull", "--ff-only", "origin", "main")
        Path("all.m3u").write_text("fresh\n")
        Path("other.txt").write_text("unrelated\n")
        with self.assertRaisesRegex(RuntimeError, "Unstaged"):
            publisher.publish("refresh", ["all.m3u"])
        self.assertEqual(self.run_git(self.remote, "show", "main:all.m3u"), "old")


if __name__ == "__main__":
    unittest.main()
