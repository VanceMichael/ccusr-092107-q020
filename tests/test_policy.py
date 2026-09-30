import unittest
from pathlib import Path

from src.context import load_policy

POLICY_PATH = Path("fixtures/policy.json")


class PolicyTest(unittest.TestCase):
    def setUp(self):
        self.data = load_policy(POLICY_PATH)

    def test_domain_and_version(self):
        self.assertEqual(self.data["domain"], "minor-ai-safeguarding")
        self.assertGreaterEqual(self.data["version"], 1)

    def test_three_pathways(self):
        keys = {p["key"] for p in self.data["pathways"]}
        self.assertEqual(
            keys,
            {
                "ordinary_emotional_expression",
                "sustained_isolation_tendency",
                "urgent_harm_risk",
            },
        )

    def test_urgent_pathway_always_hands_off_to_human(self):
        urgent = next(
            p for p in self.data["pathways"] if p["key"] == "urgent_harm_risk"
        )
        self.assertTrue(urgent["human_handoff"])

    def test_duration_cannot_be_labeling_basis_for_isolation(self):
        isolation = next(
            p
            for p in self.data["pathways"]
            if p["key"] == "sustained_isolation_tendency"
        )
        self.assertEqual(isolation["labeling_basis"], "duration_only_prohibited")

    def test_retention_raw_deleted_before_summary_expiry(self):
        for item in self.data["data_categories"]:
            self.assertLessEqual(
                item["raw_content_deleted_after_days"],
                item["retention_days"],
                msg=f"数据类别 {item['key']} 原始内容删除期限不得晚于摘要期限",
            )

    def test_traceable_events_cover_all_five(self):
        keys = {e["key"] for e in self.data["traceable_events"]}
        self.assertEqual(
            keys,
            {
                "guardianship_change",
                "consent_withdrawal",
                "in_out_of_school_account_merge",
                "false_positive_appeal",
                "night_shift_handover",
            },
        )

    def test_safeguard_flags(self):
        self.assertTrue(self.data["rule_versioning"]["prior_dispositions_frozen"])
        self.assertTrue(self.data["human_handoff"]["advance_notice_to_child"])
        view = self.data["educator_view"]
        self.assertTrue(view["shows_support_actions_only"])
        self.assertTrue(view["no_unverified_diagnosis"])
        material = self.data["desensitized_event_material"]
        self.assertTrue(material["used_for_boundary_calibration"])
        self.assertTrue(material["not_used_for_individual_labeling"])


if __name__ == "__main__":
    unittest.main()
