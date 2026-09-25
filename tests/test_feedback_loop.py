import copy
import json
from pathlib import Path
import unittest
from feedback_loop import apply_plan, digest, observations, propose, regression_check


class LoopTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1] / "fixtures"
        self.config, self.rows, self.golden = [json.loads((root / n).read_text()) for n in ("config.json", "feedback.json", "golden.json")]
        self.now = "2026-01-08T00:00:00Z"

    def plan(self):
        return propose(self.config, self.rows, self.now)

    def approval(self, plan):
        return {"plan_sha256": digest(plan), "suite_sha256": digest(self.golden), "approved": True}

    def test_approved_change_has_receipt_without_mutating_inputs(self):
        before = copy.deepcopy(self.config)
        plan = self.plan()
        after, receipt = apply_plan(self.config, self.rows, plan, self.approval(plan), self.golden)
        self.assertEqual(after["summary.max_bullets"], 3)
        self.assertTrue(after["agent.outbound_approval_required"])
        self.assertEqual(self.config, before)
        self.assertEqual(receipt["after_sha256"], digest(after))

    def test_protected_setting_is_held(self):
        self.assertEqual(self.plan()["held"], [{"id": "synthetic-4", "reason": "protected-or-unknown-setting"}])

    def test_repeated_event_does_not_inflate_support(self):
        rows = [self.rows[0]] * 5
        self.assertEqual(len(observations(rows, self.now)), 1)
        self.assertEqual(propose(self.config, rows, self.now)["changes"], [])

    def test_same_session_does_not_count_as_independent_support(self):
        for row in self.rows:
            row["session"] = "same-session"
        self.assertEqual(self.plan()["changes"], [])

    def test_conflicting_directions_are_held(self):
        self.rows.append(dict(self.rows[0], id="opposing", session="new-session", value=2))
        self.assertEqual(self.plan()["changes"], [])
        self.assertIn("conflicting-directions", [h["reason"] for h in self.plan()["held"]])

    def test_future_naive_and_malformed_rows_are_rejected(self):
        for date in ("2027-01-01T00:00:00Z", "2026-01-05T00:00:00", "not-a-date"):
            with self.assertRaises(ValueError):
                observations([dict(self.rows[0], at=date)], self.now)
        with self.assertRaises(ValueError):
            observations([{"id": "missing-fields"}], self.now)

    def test_stale_rows_are_excluded(self):
        self.assertEqual(propose(self.config, self.rows, "2026-02-01T00:00:00Z")["changes"], [])

    def test_conflicting_ids_fail(self):
        with self.assertRaises(ValueError):
            observations([self.rows[0], dict(self.rows[0], value=2)], self.now)

    def test_missing_and_stale_approvals_fail(self):
        plan = self.plan()
        for approval in ({}, {"approved": True}, dict(self.approval(plan), plan_sha256="stale"),
                         dict(self.approval(plan), approved=1)):
            with self.assertRaises(ValueError):
                apply_plan(self.config, self.rows, plan, approval, self.golden)

    def test_changed_config_and_feedback_invalidate_plan(self):
        plan = self.plan()
        with self.assertRaises(ValueError):
            apply_plan(dict(self.config, **{"summary.max_bullets": 5}), self.rows, plan, self.approval(plan), self.golden)
        with self.assertRaises(ValueError):
            apply_plan(self.config, self.rows[:-1], plan, self.approval(plan), self.golden)

    def test_modified_plan_is_not_authority_even_with_matching_approval(self):
        plan = self.plan()
        plan["changes"][0]["after"] = 2
        with self.assertRaises(ValueError):
            apply_plan(self.config, self.rows, plan, self.approval(plan), self.golden)

    def test_changed_suite_invalidates_approval(self):
        plan = self.plan()
        approval = self.approval(plan)
        self.golden.pop()
        with self.assertRaises(ValueError):
            apply_plan(self.config, self.rows, plan, approval, self.golden)

    def test_approved_change_that_loses_required_facts_is_rejected(self):
        for row in self.rows[:3]:
            row["value"] = 1
        plan = self.plan()
        with self.assertRaisesRegex(ValueError, "regression failed"):
            apply_plan(self.config, self.rows, plan, self.approval(plan), self.golden)
        self.assertEqual(self.config["summary.max_bullets"], 4)

    def test_empty_suite_and_out_of_range_values_do_not_pass(self):
        with self.assertRaises(ValueError):
            regression_check(self.config, [])
        for row in self.rows[:3]:
            row["value"] = 99
        self.assertEqual(self.plan()["changes"], [])

    def test_input_order_does_not_change_proposal(self):
        self.assertEqual(self.plan(), propose(self.config, list(reversed(self.rows)), self.now))


if __name__ == "__main__":
    unittest.main()
