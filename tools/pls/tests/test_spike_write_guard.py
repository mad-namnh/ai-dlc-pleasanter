"""The spike scripts write only to dev: a declared role other than dev is refused before the localhost exemption
(an SSH tunnel makes any server look like 127.0.0.1):
python -m unittest discover -s tools/pls/tests -v"""
import importlib.util
import unittest
from pathlib import Path

COMMON = Path(__file__).resolve().parents[3] / "spike/round-trip/scripts/common.py"
spec = importlib.util.spec_from_file_location("spike_common", COMMON)
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)


def env(url, **kw):
    return {"name": "e", "base_url": url, **kw}


class SpikeWriteGuard(unittest.TestCase):
    def refused(self, e):
        with self.assertRaises(common.UnsafeTargetError):
            common.assert_writable(e)

    def test_a_non_dev_role_is_refused_even_on_localhost(self):
        for role in ("prod", "stg", "production", "", "DEV"):
            for url in ("http://localhost:8080", "http://127.0.0.1", "https://x.localhost"):
                self.refused(env(url, role=role, allow_write=True))

    def test_localhost_with_role_dev_or_no_role_is_writable(self):
        common.assert_writable(env("http://localhost:8080", role="dev"))
        common.assert_writable(env("http://127.0.0.1"))

    def test_another_host_needs_role_dev_and_allow_write(self):
        common.assert_writable(env("https://dev.example", role="dev", allow_write=True))
        self.refused(env("https://dev.example", role="dev"))
        self.refused(env("https://dev.example", role="dev", allow_write="true"))
        self.refused(env("https://dev.example", allow_write=True))
        self.refused(env("https://prod.example", role="prod", allow_write=True))


if __name__ == "__main__":
    unittest.main()
