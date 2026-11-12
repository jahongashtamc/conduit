"""Pipeline (vazifa zanjiri) testlari — DB qatlamini tekshiradi."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pipeline


class PipelineTest(unittest.TestCase):
    def setUp(self):
        pipeline.init_pipeline_db()

    def test_create_and_get(self):
        pipe = pipeline.create_pipeline(
            [
                {"agent": "scout", "prompt": "sahifani tekshir"},
                {"agent": "painter", "prompt": "tekstura chiz"},
            ],
            name="test zanjir",
        )
        got = pipeline.get_pipeline(pipe["pipeline_id"])
        self.assertIsNotNone(got)
        self.assertEqual(got["status"], "running")
        self.assertEqual(len(got["steps"]), 2)
        self.assertEqual(got["steps"][0]["agent"], "scout")

    def test_validation_rejects_empty(self):
        with self.assertRaises(ValueError):
            pipeline.create_pipeline([])

    def test_validation_rejects_missing_fields(self):
        with self.assertRaises(ValueError):
            pipeline.create_pipeline([{"agent": "scout"}])

    def test_list_includes_newest(self):
        pipeline.create_pipeline([{"agent": "scout", "prompt": "a"}], name="bir")
        items = pipeline.list_pipelines()
        self.assertTrue(any(p["name"] == "bir" for p in items))

    def test_update_status(self):
        pipe = pipeline.create_pipeline([{"agent": "scout", "prompt": "a"}])
        pipeline._update(pipe["pipeline_id"], status="completed")
        self.assertEqual(pipeline.get_pipeline(pipe["pipeline_id"])["status"], "completed")


if __name__ == "__main__":
    unittest.main()
