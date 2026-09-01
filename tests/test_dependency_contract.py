import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DependencyContractTests(unittest.TestCase):
    def test_adk_271_compatible_pins(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        constraints = (ROOT / "constraints-python312.txt").read_text(encoding="utf-8")
        for pin in (
            "fastapi==0.139.2",
            "uvicorn[standard]==0.51.0",
            "pydantic==2.13.4",
            "google-adk==2.7.1",
            "google-auth[pyopenssl]==2.56.0",
        ):
            self.assertIn(pin, requirements)
        self.assertIn("starlette==1.3.1", constraints)
        self.assertNotIn("fastapi==0.116.1", requirements)
        self.assertNotIn("pydantic==2.11.7", requirements)
        self.assertNotIn("google-auth==2.40.3", requirements)

    def test_windows_scripts_do_not_require_posix_activation(self):
        setup = (ROOT / "scripts" / "setup_windows.cmd").read_text(encoding="utf-8")
        run = (ROOT / "scripts" / "run_windows.cmd").read_text(encoding="utf-8")
        self.assertIn("py -3.12 -m venv --clear .venv", setup)
        self.assertIn('.venv\\Scripts\\python.exe', setup)
        self.assertNotIn("source .venv/bin/activate", setup)
        self.assertIn("-m uvicorn app.main:app", run)


if __name__ == "__main__":
    unittest.main()
