"""A bounded, offline feedback-to-configuration example using synthetic inputs.

Free-form feedback is intentionally not executable. A human or a separate judge
must classify it into structured observations before this deterministic stage.
"""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be text")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return dt.astimezone(timezone.utc)


def validate_config(config):
    if set(config) != {"summary.max_bullets", "agent.outbound_approval_required"}:
        raise ValueError("unexpected configuration keys")
    if type(config["summary.max_bullets"]) is not int or not 1 <= config["summary.max_bullets"] <= 8:
        raise ValueError("bullet budget must be an integer from 1 to 8")
    if config["agent.outbound_approval_required"] is not True:
        raise ValueError("this example cannot disable outbound approval")


def observations(rows, now):
    """Reject incomplete/conflicting records; exact retries count once."""
    end = timestamp(now)
    by_id = {}
    required = {"id", "session", "at", "key", "value"}
    for row in rows:
        if not isinstance(row, dict) or set(row) != required:
            raise ValueError("observation schema mismatch")
        for key in ("id", "session", "key"):
            if not isinstance(row[key], str) or not row[key].strip():
                raise ValueError("missing observation identity")
        when = timestamp(row["at"])
        if when > end:
            raise ValueError("future observation")
        identity = row["id"]
        if identity in by_id and digest(by_id[identity]) != digest(row):
            raise ValueError("conflicting observation ID")
        digest(row)  # require finite, JSON-serializable values
        by_id[identity] = copy.deepcopy(row)
    return sorted((r for r in by_id.values() if timestamp(r["at"]) >= end - timedelta(days=7)),
                  key=lambda r: r["id"])


def propose(config, rows, now):
    validate_config(config)
    recent = observations(rows, now)
    groups, held = {}, []
    for row in recent:
        value = row["value"]
        if row["key"] != "summary.max_bullets":
            held.append({"id": row["id"], "reason": "protected-or-unknown-setting"})
        elif type(value) is not int or not 1 <= value <= 8:
            held.append({"id": row["id"], "reason": "out-of-range"})
        else:
            groups.setdefault(value, []).append(row)
    changes = []
    if len(groups) > 1:
        # Opposing signals need judgment, even if one side has more votes.
        held.extend({"id": r["id"], "reason": "conflicting-directions"} for rows_for_value in groups.values() for r in rows_for_value)
    elif groups:
        value, support = next(iter(groups.items()))
        if len({r["session"] for r in support}) < 3:
            held.extend({"id": r["id"], "reason": "need-three-distinct-sessions"} for r in support)
        elif value != config["summary.max_bullets"]:
            changes.append({"key": "summary.max_bullets", "before": config["summary.max_bullets"],
                            "after": value, "evidence": [r["id"] for r in support]})
    return {"version": 1, "as_of": now, "base_sha256": digest(config),
            "feedback_sha256": digest(recent), "changes": changes,
            "held": sorted(held, key=lambda r: r["id"])}


def render_summary(items, config):
    """Tiny formatter: required facts go first, then optional context within budget."""
    validate_config(config)
    ordered = [i for i in items if i["required"]] + [i for i in items if not i["required"]]
    return [i["text"] for i in ordered[:config["summary.max_bullets"]]]


def regression_check(config, fixtures):
    if not fixtures:
        raise ValueError("empty regression suite")
    failures = []
    for case in fixtures:
        actual = render_summary(case["items"], config)
        required = {i["text"] for i in case["items"] if i["required"]}
        if not required.issubset(actual) or len(actual) > config["summary.max_bullets"]:
            failures.append(case["name"])
    return {"passed": not failures, "failures": failures,
            "suite_sha256": digest(fixtures), "candidate_sha256": digest(config)}


def apply_plan(config, rows, plan, approval, fixtures):
    """Return a candidate and receipt. Never edit the caller's files or dictionaries."""
    validate_config(config)
    if plan != propose(config, rows, plan["as_of"]):
        raise ValueError("stale or modified plan")
    if (not isinstance(approval, dict) or approval.get("approved") is not True
            or approval != {"plan_sha256": digest(plan), "suite_sha256": digest(fixtures), "approved": True}):
        raise ValueError("missing or stale approval")
    if not plan["changes"]:
        raise ValueError("no qualified change")
    candidate = copy.deepcopy(config)
    for change in plan["changes"]:
        candidate[change["key"]] = change["after"]
    check = regression_check(candidate, fixtures)
    if not check["passed"]:
        raise ValueError("regression failed: " + ", ".join(check["failures"]))
    receipt = {"status": "accepted", "plan_sha256": digest(plan),
               "before_sha256": digest(config), "after_sha256": digest(candidate),
               "regression": check}
    return candidate, receipt
