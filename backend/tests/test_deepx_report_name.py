"""DeepX hisobot nomi uzun prompt'larda ham Windows chegarasiga sig'ishi kerak."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.deepx import DeepXAnalyzer  # noqa: E402


def test_long_topic_report_filename_is_bounded(tmp_path):
    analyzer = DeepXAnalyzer(workspace_root=str(tmp_path))
    topic = "Nexus Studiyasida umumiy xatolar " + "va kamchiliklar " * 30
    path = analyzer.generate_research_report(topic, [])
    name = os.path.basename(path)
    assert os.path.isfile(path)
    assert len(name) <= 90
    assert name.startswith("nexus_studiyasida_umumiy_xatolar")
    assert name.endswith(".md")
