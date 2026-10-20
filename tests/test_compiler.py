import tempfile
import unittest
import sys
from pathlib import Path
from difftest.compiler import run_command, test_configuration
from difftest.config import CompilerConfig

class CompilerTests(unittest.TestCase):
    def test_run_command_success(self):
        result = run_command([sys.executable, "-c", "print('hello')"], 3)
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["stdout"], "hello\n")
        self.assertFalse(result["timed_out"])
    def test_run_command_timeout(self):
        result = run_command([sys.executable, "-c", "import time; time.sleep(2)"], 1)
        self.assertTrue(result["timed_out"])
    def test_missing_executable(self):
        self.assertIsNotNone(run_command(["/definitely/not/a/compiler"], 2)["launch_error"])
    def test_compile_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "test.c"
            source.write_text("int main(void) { return 0; }")
            cfg = CompilerConfig("fake", "/usr/bin/false", "O0")
            result = test_configuration(cfg, source, Path(temp) / "out", temp, 3, 3)
            self.assertEqual(result["compile_status"], "compile_error")

if __name__ == "__main__":
    unittest.main()
