import json
import unittest
from pathlib import Path

from src.context import load_context

FIXTURE = Path("fixtures/context.json")


class ContextTest(unittest.TestCase):
    def setUp(self):
        self.data = load_context(FIXTURE)

    def test_fixture_matches_domain(self):
        self.assertEqual(self.data["domain"], "minor-ai-safeguarding")
        self.assertGreaterEqual(len(self.data["facts"]), 1)

    def test_version_bumped(self):
        self.assertGreaterEqual(self.data["version"], 2)

    def test_collected_data_is_minimum_set(self):
        codes = {item["code"] for item in self.data["collected_data"]}
        self.assertEqual(
            codes,
            {
                "usage-window",
                "risk-signal",
                "help-request",
                "guardian-authorization",
                "school-authorization",
                "human-care-outcome",
            },
        )

    def test_triage_paths_are_separate(self):
        paths = {item["code"]: item for item in self.data["triage_paths"]}
        # 三类路径互不合并，紧急路径必须指向真人响应。
        self.assertEqual(
            set(paths),
            {"ordinary-emotion", "persistent-isolation", "urgent-harm"},
        )
        self.assertIn("真人", paths["urgent-harm"]["path"])
        self.assertNotIn("升级", paths["ordinary-emotion"]["path"])

    def test_retention_rules_cover_deletion_and_no_retroactivity(self):
        rules = self.data["retention_rules"]
        self.assertIn("删除", rules["raw_content"])
        self.assertIn("期限", rules["necessary_summary"])
        self.assertIn("不改写", rules["rule_versions"])

    def test_traceable_events_cover_lifecycle(self):
        codes = {item["code"] for item in self.data["traceable_events"]}
        self.assertEqual(
            codes,
            {
                "guardianship-change",
                "consent-withdrawal",
                "account-merge",
                "false-positive-appeal",
                "night-handover",
            },
        )

    def test_safeguards_cover_handoff_notice_and_teacher_view(self):
        by_code = {item["code"]: item for item in self.data["safeguards"]}
        self.assertIn("提前告知", by_code["handoff-notice"]["statement"])
        self.assertIn("支持行动", by_code["teacher-view"]["statement"])
        self.assertIn("使用时长", by_code["no-duration-label"]["statement"])

    def test_boundary_materials(self):
        codes = {item["code"] for item in self.data["boundary_materials"]}
        self.assertEqual(codes, {"age-bands", "de-identified-events"})

    def test_fixture_is_valid_json_and_schema_shaped(self):
        raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
        # additionalProperties: false 约束下不应出现未约定字段。
        expected = {
            "domain", "version", "facts", "sample_id", "collection_principle",
            "collected_data", "triage_paths", "retention_rules",
            "boundary_materials", "traceable_events", "safeguards",
        }
        self.assertEqual(set(raw), expected)


if __name__ == "__main__":
    unittest.main()
