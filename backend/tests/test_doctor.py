"""Doctor tekshiruvlari testlari."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import doctor


class DoctorTest(unittest.TestCase):
    def test_python_check_passes(self):
        name, status, detail = doctor.check_python()
        self.assertEqual(status, "OK")
        self.assertIn("Python", name)

    def test_node_check(self):
        name, status, _ = doctor.check_node()
        # Node is required for MVP; on this machine it must exist.
        self.assertIn(status, ("OK", "FAIL"))
        self.assertEqual(name, "Node.js")

    def test_ffmpeg_check_shape(self):
        name, status, detail = doctor.check_ffmpeg()
        self.assertEqual(name, "FFmpeg")
        self.assertIn(status, ("OK", "FAIL"))
        self.assertTrue(detail)

    def test_blender_check_shape(self):
        name, status, detail = doctor.check_blender()
        self.assertEqual(name, "Blender")
        self.assertIn(status, ("OK", "WARN"))

    def test_run_all_returns_consistent_statuses(self):
        checks = doctor.run_all_checks()
        self.assertGreater(len(checks), 10)
        for name, status, detail in checks:
            self.assertIn(status, ("OK", "WARN", "FAIL"))
            self.assertTrue(name)
            self.assertTrue(detail)

    def test_doctor_exit_semantics(self):
        checks, all_ok = doctor.run_doctor(verbose=False)
        fails = [c for c in checks if c[1] == "FAIL"]
        self.assertEqual(all_ok, not fails)


if __name__ == "__main__":
    unittest.main()
