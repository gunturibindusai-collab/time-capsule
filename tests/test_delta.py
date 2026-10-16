import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.delta_engine import make_delta, apply_delta

class DeltaTests(unittest.TestCase):
    def test_round_trips(self):
        cases = [
            ("hello world\n", "hello brave world\n"),
            ("abc\ndef\nxyz\n", "abc\nXYZ\n"),
            ("", "first version"),
            ("first version", ""),
            ("same", "same"),
            ("Tamil: வணக்கம் 🌱\n", "Tamil: வணக்கம்! 🌱\n"),
            ("a\r\nb\r\n", "a\r\nchanged\r\n"),
        ]
        for old, new in cases:
            with self.subTest(old=old, new=new):
                self.assertEqual(apply_delta(old, make_delta(old, new)), new)

    def test_rejects_malformed_delta(self):
        with self.assertRaises(ValueError):
            apply_delta("extra", b'[["e",1,""]]')

if __name__ == "__main__": unittest.main()
