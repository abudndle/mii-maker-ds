#!/usr/bin/env python3
"""Synthetic-only regression for private Mii Maker ZIP validation acceleration."""
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
cache=importlib.import_module("private_validation_cache")
builder=importlib.import_module("build_private")


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/"source").mkdir()
        (self.root/"tools").mkdir()
        (self.root/"tests").mkdir()
        (self.root/"source/main.c").write_text("int main(void){return 0;}\n")
        (self.root/"tools/verify.py").write_text("print('source')\n")
        self.asset=self.root/"my-private.zip"
        with ZipFile(self.asset,"w") as z:
            z.writestr("nitrofiles/fake.bin",b"synthetic-not-a-Nintendo-asset")

    def test_content_addressed_hit_and_invalidation(self):
        self.assertFalse(cache.cache_hit(self.root,self.asset))
        cache.cache_store(self.root,self.asset)
        self.assertTrue(cache.cache_hit(self.root,self.asset))
        record=json.loads((self.root/cache.CACHE_RELATIVE).read_text())
        self.assertEqual(set(record),{
            "version","archive_size","archive_sha256","source_sha256"})
        self.assertNotIn(str(self.asset),str(record))
        (self.root/"source/main.c").write_text("int main(void){return 1;}\n")
        self.assertFalse(cache.cache_hit(self.root,self.asset))
        cache.cache_store(self.root,self.asset)
        self.assertTrue(cache.cache_hit(self.root,self.asset))
        (self.root/"tools/verify.py").write_text("print('changed')\n")
        self.assertFalse(cache.cache_hit(self.root,self.asset))
        cache.cache_store(self.root,self.asset)
        with ZipFile(self.asset,"a") as z:
            z.writestr("nitrofiles/another.bin",b"more synthetic content")
        self.assertFalse(cache.cache_hit(self.root,self.asset))

    def test_damaged_cache_and_empty_archive_are_rejected(self):
        cache.cache_store(self.root,self.asset)
        (self.root/cache.CACHE_RELATIVE).write_text('not JSON')
        self.assertFalse(cache.cache_hit(self.root,self.asset))
        self.asset.write_bytes(b"")
        with self.assertRaisesRegex(ValueError,"empty"):
            cache.fingerprint(self.root,self.asset)

    def test_full_validator_runs_once_and_bypass_rechecks(self):
        # Patch only the private cache's root for a wholly synthetic fixture;
        # full original-format validators are deliberately not run here.
        with patch.object(builder,"ROOT",self.root),\
             patch.object(builder,"validate",return_value=0) as validate,\
             patch.object(builder,"run") as run:
            builder.check_zip(self.asset)
            self.assertEqual(validate.call_count,1)
            self.assertEqual(run.call_count,3)
            builder.check_zip(self.asset)
            self.assertEqual(validate.call_count,1) # cached
            self.assertEqual(run.call_count,3)
            builder.check_zip(self.asset,use_cache=False)
            self.assertEqual(validate.call_count,2) # explicit recheck
            self.assertEqual(run.call_count,6)

    def test_failed_private_validation_cannot_leave_success_stamp(self):
        with patch.object(builder,"ROOT",self.root),\
             patch.object(builder,"validate",return_value=1):
            with self.assertRaisesRegex(ValueError,"invalid"):
                builder.check_zip(self.asset)
        self.assertFalse(cache.cache_hit(self.root,self.asset))


if __name__=="__main__":
    unittest.main()
