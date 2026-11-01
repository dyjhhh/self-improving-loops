# Self-Improving Loops

**Problem:** corrections to an agent tend to stay buried in old conversations instead of becoming changes anyone can inspect.\
**What it shows:** a correction loop with a hard stop. Three requests for shorter summaries become one proposed change; a request to disable outbound approval is held for a person.\
**Run it in about 60 seconds:** clone, then `make test` (Python 3.10+; no model key or third-party package).

[![tests](https://github.com/dyjhhh/self-improving-loops/actions/workflows/test.yml/badge.svg)](https://github.com/dyjhhh/self-improving-loops/actions/workflows/test.yml)

## Applying this on an engineering team

- **Feedback to configuration with an audit trail.** Repeated corrections are grouped into one proposed parameter change, and the receipt records the plan hash and the before and after configuration hashes.
- **Approval by risk.** Policy keys that govern external actions are excluded from automatic proposals; the example refuses to disable outbound approval.
- **Recheck at approval time.** The plan is recomputed against the current configuration and feedback, so an approval for a stale plan is rejected.
- **Regression check before rollout.** The candidate runs against a golden set, and an empty suite fails instead of passing.

In the harness I run, corrections go through scheduled feedback collection, bounded review, and reports with an explicit place to be read.

This repository makes a small part of that process runnable: structured feedback, then a proposal, approval, a regression check, and a candidate configuration with its receipt.

## Try it

To run the demo and each suite separately:

```sh
python3 demo.py
python3 -m unittest discover -s tests -v
python3 tools/test_sensitivity_scan.py
```

The fictional operator asks for shorter summaries in three separate sessions. The loop proposes changing the bullet budget from four to three. A separate request to disable outbound approval is held. The demo first shows approval missing, then supplies a clearly labeled simulated approval and checks the candidate against a small golden set.

**No live agent, file, configuration or account is changed.** All input data and approval are synthetic. The returned configuration is an in-memory value.

## What the implementation checks

| Stage | Boundary |
|---|---|
| Harvest | Time-bounded structured observations; conflicting IDs and future timestamps fail |
| Group | Exact retries count once; repeated messages in one session cannot create three-session support |
| Propose | Only the summary bullet budget is tunable; opposing directions are held for judgment |
| Approve | Approval identifies the exact plan and regression suite by hash |
| Recheck | Recompute the plan against the current configuration and feedback before accepting it |
| Test | Required facts must survive the shorter output; an empty regression suite fails |
| Return | Produce the candidate plus a receipt with plan and before/after configuration hashes, leaving the original unchanged |

Read [`feedback_loop.py`](feedback_loop.py), the [synthetic fixtures](fixtures), and the [tests](tests/test_feedback_loop.py). [Design notes](docs/design.md) explain why each boundary exists and what a passing check does not show. [`tools/sensitivity-scan.sh`](tools/sensitivity-scan.sh) is a pre-publication pattern check for this repository, not part of the loop.

## Scope and limits

- The input is already classified. Natural-language interpretation and the quality of that classification are outside this example.
- Three sessions is an illustrative threshold, not statistical confidence or proof that the user wants a change. Sessions are supplied by a trusted caller and can be fabricated.
- Hashes detect changed inputs; they do not authenticate an approver, and approvals do not expire (the recheck uses the plan's own `as_of` time). The approval dictionary in the demo is a fixture, not a real user's permission.
- The regression suite checks a tiny deterministic formatter. It does not measure a language model's output quality or prove general improvement.
- Policy keys governing external actions are excluded from automatic proposals here. The example contains no outbound tools, autonomous self-editing, or model training.
- A production consumer must verify identity and authorization, write configuration atomically, monitor results, and provide rollback. This repository stops at a tested candidate and receipt.

The older system used local feedback files, private logs, and scheduled model-assisted review. This public edition replaces those inputs with fictional records and adds explicit version checks. It does not claim that the demo is the deployed system. In the private system, low-risk presentation changes are applied and reported afterward, while anything touching meaning, money or outbound messages waits for my decision. This edition requires explicit approval for every change, so the approval step itself can be tested.

## Related work

[Agent OS](https://github.com/dyjhhh/agent-os) · [Evaluation gates](https://github.com/dyjhhh/agent-eval-gates) · [Reliability](https://github.com/dyjhhh/agent-reliability) · [Security hooks](https://github.com/dyjhhh/agent-security-hooks) · [Award alerts](https://github.com/dyjhhh/award-alert-bridge) · [Careers watch](https://github.com/dyjhhh/careers-watch)

Personal project by Yujia Dong · AI-assisted development. Design choices and review are mine; Claude Code and Codex assisted with implementation, including the public extraction and tests.

MIT license. See [LICENSE](LICENSE).
