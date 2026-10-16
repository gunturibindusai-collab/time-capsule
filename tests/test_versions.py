import sys, unittest, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.version_manager import new_capsule, add_version, reconstruct_version, storage_stats, capsule_archive_bytes, validate_capsule

class VersionTests(unittest.TestCase):
    def test_versions_reconstruct_and_verify(self):
        c = new_capsule("test", "app.py")
        texts = ["print('hello')\n", "print('hello world')\n", "# comment\nprint('hello world')\n"]
        for i, text in enumerate(texts): add_version(c, text, f"v{i+1}")
        for i, text in enumerate(texts): self.assertEqual(reconstruct_version(c, i), text)
        self.assertEqual(storage_stats(c)["version_count"], 3)
        validate_capsule(json.loads(capsule_archive_bytes(c).decode("utf-8")))

if __name__ == "__main__": unittest.main()
