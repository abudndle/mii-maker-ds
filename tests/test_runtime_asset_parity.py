"""Asset-free NitroFS runtime resource coverage and format regressions."""
import importlib.util
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
spec = importlib.util.spec_from_file_location('verify_runtime_assets', TOOLS / 'verify_runtime_assets.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RuntimeAssets(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        source = self.root / 'source'
        source.mkdir()
        fields = ','.join('{"Field",1,0}' for _ in range(62))
        (source / 'avatar.c').write_text(f'const MdsField mds_fields[MDS_FIELDS]={{{fields}}};')
        rows = '\n'.join(f'{{"Edit{i}","Icon{i}",2,{i},2,{{{{}}}}}},' for i in range(12))
        rows += '\n{"EditBody",NULL,2,12,0,{}},'
        (source / 'ui_generated.h').write_text('static const UiCategory ui_categories[]={\n'+rows+'\n};')
        (source / 'ui.c').write_text("""
        char *a="nitro:/ui/home-bottom.rgb555";
        char *b="nitro:/art/StatusPersonal.bin";
        char *c="nitro:/art/%s%0*d.bin";
        char *d="nitro:/ui/%s.rgb555";
        char *e="nitro:/test-import";""")
        self.names,_ = module.source_paths(self.root)
        self.packed = {}
        for name in self.names:
            if name.startswith('ui/'):
                self.packed[name] = bytes(module.UI_BYTES)
            elif name.startswith('art/'):
                self.packed[name] = (3).to_bytes(2,'little') + (2).to_bytes(2,'little') + bytes(12)
            else:
                self.packed[name] = b'private synthetic fixture only'
        self.archive = self.root / 'fixture.zip'

    def write_archive(self):
        with zipfile.ZipFile(self.archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            for name, value in self.packed.items():
                z.writestr('nitrofiles/'+name,value)
        return self.archive

    def test_complete_fixture(self):
        summary=module.verify(self.write_archive(),self.root)
        self.assertEqual(summary['feature_icons'],25)
        self.assertEqual(summary['backgrounds'],13)
        self.assertEqual(summary['verified_ui_bitmaps'],14)
        self.assertEqual(summary['verified_art_sprites'],26)
        self.assertEqual(summary['runtime_assets'],40)

    def test_missing_final_sprite(self):
        self.packed.pop('art/Icon11'+'01.bin')
        with self.assertRaisesRegex(ValueError,'missing'):
            module.verify(self.write_archive(),self.root)

    def test_corrupt_background(self):
        self.packed['ui/Edit5.rgb555']=bytes(12)
        with self.assertRaisesRegex(ValueError,'RGB555 screen dimensions'):
            module.verify(self.write_archive(),self.root)

    def test_corrupt_art_dimensions(self):
        self.packed['art/Icon000.bin']=b'\x00\x00\x02\x00'+bytes(12)
        with self.assertRaisesRegex(ValueError,'sprite header/payload'):
            module.verify(self.write_archive(),self.root)

    def test_truncated_art(self):
        self.packed['art/Icon101.bin']=b'\x01\x00\x01\x00\xff'
        with self.assertRaisesRegex(ValueError,'feature sprite size'):
            module.verify(self.write_archive(),self.root)

    def test_duplicate_zip_path(self):
        self.write_archive()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.archive,'a') as z:
                z.writestr('nitrofiles/art/Icon001.bin',b'fake')
        with self.assertRaisesRegex(ValueError,'Unsafe/duplicate'):
            module.verify(self.archive,self.root)

    def test_dynamic_template_drift(self):
        path=self.root/'source/ui.c'
        path.write_text(path.read_text().replace('nitro:/ui/%s.rgb555','nitro:/ui/%d.rgb555'))
        with self.assertRaisesRegex(ValueError,'dynamic NitroFS'):
            module.source_paths(self.root)

    def test_field_count_drift(self):
        path=self.root/'source/avatar.c'
        path.write_text(path.read_text().replace('{"Field",1,0}', '', 1))
        with self.assertRaisesRegex(ValueError,'field count changed'):
            module.source_paths(self.root)

    def test_wrong_category_maximum(self):
        path=self.root/'source/ui_generated.h'
        path.write_text(path.read_text().replace('"Edit5","Icon5",2,5,2', '"Edit5","Icon5",2,200,2'))
        with self.assertRaisesRegex(ValueError,'Unsafe editor category'):
            module.source_paths(self.root)

    def test_missing_runtime_static(self):
        self.packed.pop('ui/home-bottom.rgb555')
        with self.assertRaisesRegex(ValueError,'missing'):
            module.verify(self.write_archive(),self.root)


if __name__=='__main__':
    unittest.main()
