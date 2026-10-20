import unittest
from difftest.classifier import PASS, MISMATCH, COMPILE_DIFF, COMPILE_FAIL, TIMEOUT, RUNTIME_FAIL, INCONCLUSIVE, classify

def outcome(compile_status="ok", run_status="ok", rc=0, out="checksum=123\n"):
    return {"compile_status": compile_status, "run_status": run_status,
            "returncode": rc, "stdout": out}

class ClassifyTests(unittest.TestCase):
    def test_all_agree_passes(self):
        self.assertEqual(classify({"gcc-O0": outcome(), "clang-O2": outcome()})[0], PASS)
    def test_stdout_difference_is_mismatch(self):
        self.assertEqual(classify({"gcc-O0": outcome(out="123"), "clang-O2": outcome(out="456")})[0], MISMATCH)
    def test_exit_code_difference_is_mismatch(self):
        self.assertEqual(classify({"gcc-O0": outcome(), "clang-O2": outcome(rc=1)})[0], MISMATCH)
    def test_completed_mismatch_not_hidden_by_timeout(self):
        cases = {"gcc-O0": outcome(out="a"), "clang-O2": outcome(out="b"),
                 "gcc-O3": outcome(run_status="timeout", rc=None, out="")}
        self.assertEqual(classify(cases)[0], MISMATCH)
    def test_compile_difference(self):
        cases = {"gcc-O0": outcome(), "clang-O2": outcome("compile_error", "not_run", None, "")}
        self.assertEqual(classify(cases)[0], COMPILE_DIFF)
    def test_all_compile_fail(self):
        cases = {"gcc-O0": outcome("compile_error", "not_run", None, ""),
                 "clang-O2": outcome("compiler_crash", "not_run", None, "")}
        self.assertEqual(classify(cases)[0], COMPILE_FAIL)
    def test_timeout(self):
        cases = {"gcc-O0": outcome(run_status="timeout", rc=None, out=""),
                 "clang-O2": outcome(run_status="timeout", rc=None, out="")}
        self.assertEqual(classify(cases)[0], TIMEOUT)
    def test_runtime_failure(self):
        cases = {"gcc-O0": outcome("ok", "nonzero_exit", 2),
                 "clang-O2": outcome("ok", "nonzero_exit", 2)}
        self.assertEqual(classify(cases)[0], RUNTIME_FAIL)
    def test_empty_is_inconclusive(self):
        self.assertEqual(classify({})[0], INCONCLUSIVE)

if __name__ == "__main__":
    unittest.main()
