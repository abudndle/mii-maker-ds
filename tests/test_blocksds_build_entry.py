#!/usr/bin/env python3
"""Synthetic-only BlocksDS smoke and local private Docker wrapper regressions."""
import importlib.util
import os
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'
sys.path.insert(0, str(TOOLS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixture = load('generate_ci_compile_assets')
docker = load('build_private_docker')


class SourceFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        src = self.root/'source'
        src.mkdir()
        fields=','.join('{"F",1,0}' for _ in range(62))
        (src/'avatar.c').write_text('const MdsField mds_fields[MDS_FIELDS]={'+fields+'};')
        rows='\n'.join('{"Edit%d","Icon%d",2,%d,2,{}}' % (i,i,i) for i in range(12))
        rows += '\n{"EditBody",NULL,2,12,0,{}}'
        (src/'ui_generated.h').write_text('static const UiCategory ui_categories[]={\n'+rows+'\n};')
        (src/'ui.c').write_text('"nitro:/ui/home-bottom.rgb555"\n'
                                 '"nitro:/art/%s%0*d.bin"\n"nitro:/ui/%s.rgb555"')
        self.env={'CI':'true','MDS_SYNTHETIC_COMPILE_ONLY':'yes'}

    def test_fixture_is_plainly_nonplayable_and_complete(self):
        count=fixture.generate(self.root,self.env)
        self.assertGreater(count,30)
        art=self.root/'nitrofiles/art/Icon001.bin'
        self.assertEqual(art.read_bytes(),b'\x01\x00\x01\x00\x00\x80')
        self.assertEqual((self.root/'nitrofiles/ui/home-bottom.rgb555').stat().st_size,98304)
        self.assertEqual((self.root/'assets/ui/original-icon.gif').read_bytes()[:6],b'GIF87a')
        self.assertFalse((self.root/'mii-ds.nds').exists())

    def test_disabled_without_explicit_ci_safety_switches(self):
        for env in ({},{'CI':'true'},{'MDS_SYNTHETIC_COMPILE_ONLY':'yes'}):
            with self.assertRaisesRegex(ValueError,'restricted'):
                fixture.generate(self.root,env)
        self.assertFalse((self.root/'nitrofiles').exists())

    def test_refuses_existing_original_resources(self):
        (self.root/'nitrofiles').mkdir()
        (self.root/'nitrofiles/private.dat').write_bytes(b'user data')
        with self.assertRaisesRegex(ValueError,'existing/private'):
            fixture.generate(self.root,self.env)
        self.assertEqual((self.root/'nitrofiles/private.dat').read_bytes(),b'user data')

    def test_refuses_existing_rom(self):
        (self.root/'mii-ds.nds').write_bytes(b'KEEP PRIVATE')
        with self.assertRaisesRegex(ValueError,'existing ROM'):
            fixture.generate(self.root,self.env)
        self.assertEqual((self.root/'mii-ds.nds').read_bytes(),b'KEEP PRIVATE')


class PrivateDockerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root/'project'
        self.project.mkdir()
        self.archive = self.root/'private.zip'
        self.archive.write_bytes(b'private synthetic archive, not actual Nintendo files')

    def test_mounts_offline_and_never_uploads(self):
        cmd=docker.command(self.archive,self.project,jobs=4)
        self.assertEqual(cmd[0:3],['docker','run','--rm'])
        self.assertIn('none',cmd)
        self.assertIn('--cap-drop',cmd)
        self.assertIn('--security-opt',cmd)
        self.assertIn('no-new-privileges',cmd)
        self.assertNotIn('/private/resources.zip',repr(cmd))
        self.assertNotIn(str(self.archive.resolve()),repr(cmd))
        self.assertIn('type=bind,source='+str(self.project.resolve())+',target=/work',cmd)
        self.assertEqual(cmd[-4:],['skylyrac/blocksds:slim-latest','SDK_STAGE=1','-j4','mii-ds.nds'])
        self.assertEqual(cmd[cmd.index('--entrypoint')+1],'make')
        self.assertNotIn('upload',repr(cmd).lower())
        self.assertNotIn('--privileged',cmd)
        self.assertEqual(self.archive.stat().st_size,len(b'private synthetic archive, not actual Nintendo files'))

    def test_validate_only_needs_no_docker_and_never_extracts(self):
        with patch.object(docker,'check_zip') as precheck, \
             patch.object(docker,'validate') as extract, \
             patch.object(docker.subprocess,'run') as compiler:
            docker.build(self.archive,validate_only=True)
        precheck.assert_called_once()
        extract.assert_not_called()
        compiler.assert_not_called()

    def test_never_accepts_docker_cli_injection(self):
        for image in ('-it', 'bad image', '', '--privileged'):
            with self.subTest(image=image),self.assertRaisesRegex(ValueError,'invalid Docker'):
                docker.command(self.archive,self.project,image=image)

    def test_rejects_missing_archive(self):
        with self.assertRaises((ValueError,OSError)):
            docker.command(self.root/'missing.zip',self.project)

    def test_rejects_unbounded_build_jobs(self):
        for jobs in (0,17):
            with self.assertRaisesRegex(ValueError,'jobs'):
                docker.command(self.archive,self.project,jobs=jobs)


if __name__ == '__main__':
    unittest.main()
