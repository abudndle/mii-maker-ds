"""Native C boundary tests for malformed Mii birthday editor state."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ProfileBirthdayEdges(unittest.TestCase):
    def test_native_date_arrows(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe=Path(tmp)/"profile-birthday"
            subprocess.run([os.environ.get("CC","cc"),"-std=c11",
                            "-Wall","-Wextra","-Werror","-Isource",
                            "tests/profile_birthday_edges.c",
                            "source/profile.c","source/avatar.c",
                            "-o",str(exe)],cwd=ROOT,check=True,timeout=30)
            subprocess.run([str(exe)],cwd=ROOT,check=True,timeout=30)
    def test_birthday_arrows_are_the_existing_editor_api(self):
        source=(ROOT/"source/profile.c").read_text()
        assert "mds_profile_date_step(p,1,1)" in source
        assert "mds_profile_date_step(p,0,-1)" in source
        func=source.split("void mds_profile_date_step(",1)[1].split(
            "int mds_profile_favorite(",1)[0]
        assert "if(!p)return;" in func
        assert "if(p->month<1||p->month>12)" in func
        assert "if(p->day<1)" in func
        assert "if(p->day>limit)" in func
        assert "int step=(delta>0)-(delta<0);" in func
if __name__=="__main__":
    unittest.main()
