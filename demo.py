"""Fictional approval and data. No live agent or configuration is changed."""
import json
from pathlib import Path
from feedback_loop import apply_plan, digest, propose


def main():
    root = Path(__file__).parent / "fixtures"
    config, feedback, golden = [json.loads((root / name).read_text()) for name in ("config.json", "feedback.json", "golden.json")]
    plan = propose(config, feedback, "2026-01-08T00:00:00Z")
    print("SYNTHETIC DEMO: structured feedback and approval are fixtures.")
    print("Proposal:", json.dumps(plan["changes"]))
    print("Held:", json.dumps(plan["held"]))
    try:
        apply_plan(config, feedback, plan, {}, golden)
    except ValueError as error:
        print("Before approval:", error)
    simulated_approval = {"plan_sha256": digest(plan), "suite_sha256": digest(golden), "approved": True}
    candidate, receipt = apply_plan(config, feedback, plan, simulated_approval, golden)
    print("With simulated approval:", json.dumps(candidate))
    print("Receipt:", json.dumps(receipt, indent=2))
    print("Original configuration remains:", json.dumps(config))


if __name__ == "__main__":
    main()
