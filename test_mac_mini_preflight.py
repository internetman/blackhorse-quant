import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import mac_mini_preflight as p

SRC=Path(__file__).resolve().parent


class PreflightTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.repo=Path(t.name)
        for rel in p.REQUIRED:
            dest=self.repo/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(SRC/rel,dest)
        self.git("init","-q")
        self.git("add",".")
        self.git("-c","user.name=fixture","-c","user.email=fixture@example.invalid","commit","-qm","Synthetic pinned checkout")
        self.sha=self.git("rev-parse","HEAD").strip()

    def git(self,*args):
        return subprocess.check_output(["/usr/bin/git","-C",str(self.repo),*args],text=True)

    def test_preview_no_install_no_network_no_private_changes(self):
        out=p.report(self.repo,self.sha,Path(sys.executable),"2026-11-16T16:40:00+08:00")
        self.assertEqual(out["status"],"preview_ok")
        self.assertEqual(out["scheduler"]["status"],"preview_no_worker")
        self.assertEqual(out["scheduler"]["targetDate"],"2026-11-16")
        self.assertEqual(out["ffdPointsUsed"],0)
        self.assertFalse(out["schedulerInstalled"] or out["workerStarted"] or out["stateCreated"] or out["networkUsed"])
        self.assertEqual(self.git("status","--porcelain=v1","--ignored"),"")

    def test_pin_and_dirty_checkout_enforced(self):
        with self.assertRaisesRegex(ValueError,"pin"):
            p.pinned_checkout(self.repo,"0"*40)
        (self.repo/"untracked.py").write_text("")
        with self.assertRaisesRegex(ValueError,"clean"):
            p.pinned_checkout(self.repo,self.sha)

    def test_refuses_ambiguous_time(self):
        with self.assertRaisesRegex(ValueError,"timezone"):
            p.report(self.repo,self.sha,Path(sys.executable),"2026-11-16T16:40:00")


if __name__ == "__main__":
    unittest.main()
