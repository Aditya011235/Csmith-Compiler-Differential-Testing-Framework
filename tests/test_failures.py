import unittest
from difftest.config import RunConfig, validate_run_config

class ConfigTests(unittest.TestCase):
    def base(self, **kwargs):
        values = dict(first=0, last=10, jobs=2, csmith="csmith",
                      include_dir="/tmp", outdir="out")
        values.update(kwargs)
        return RunConfig(**values)
    def test_valid(self):
        validate_run_config(self.base())
    def test_reversed_range(self):
        with self.assertRaises(ValueError):
            validate_run_config(self.base(first=10, last=2))
    def test_zero_jobs(self):
        with self.assertRaises(ValueError):
            validate_run_config(self.base(jobs=0))
    def test_negative_seed(self):
        with self.assertRaises(ValueError):
            validate_run_config(self.base(first=-1))

if __name__ == "__main__":
    unittest.main()
