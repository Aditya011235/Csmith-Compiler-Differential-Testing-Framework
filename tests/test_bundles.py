import json
import tempfile
import unittest
from pathlib import Path
from difftest.bundles import write_bundle

class BundleTests(unittest.TestCase):
    def test_bundle_files(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "seed_7"
            write_bundle(dest, 7, "int main(void){return 0;}\n",
                {"gcc-O0": {"compile_status": "ok", "stdout": "x"}},
                "mismatch", "different output",
                {"include_dir": "/usr/include/csmith",
                 "configurations": [{"label": "gcc-O0", "executable": "/usr/bin/gcc",
                                     "optimization": "O0"}]})
            self.assertTrue((dest / "test.c").is_file())
            self.assertTrue((dest / "repro.sh").is_file())
            self.assertEqual(json.loads((dest / "result.json").read_text())["seed"], 7)
            self.assertTrue((dest / "metadata.json").is_file())

if __name__ == "__main__":
    unittest.main()
