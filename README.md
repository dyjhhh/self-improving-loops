# Self-Improving Loops

[![tests](https://github.com/dyjhhh/self-improving-loops/actions/workflows/test.yml/badge.svg)](https://github.com/dyjhhh/self-improving-loops/actions/workflows/test.yml)

I wanted corrections to an agent's work to lead to changes I could inspect, rather than another instruction buried in a conversation. In my personal system, this led to scheduled feedback collection, bounded review, and reports with an explicit place to be read.

This repository makes a small part of that process runnable: **structured feedback → proposal → approval → regression check → candidate configuration and receipt**.

## Try it

Python 3.10 or newer. No model key or third-party package is required:

```sh
python3 demo.py
python3 -m unittest discover -s tests -v
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
| Return | Produce the candidate plus a version-linked receipt, leaving the original unchanged |

Read [`feedback_loop.py`](feedback_loop.py), the [synthetic fixtures](fixtures), and the [tests](tests/test_feedback_loop.py). [Design notes](docs/design.md) explain the separation between judgment and enforcement.

## Scope and limits

- The input is already classified. Natural-language interpretation and the quality of that classification are outside this example.
- Three sessions is an illustrative threshold, not statistical confidence or proof that the user wants a change. Sessions are supplied by a trusted caller and can be fabricated.
- Hashes detect changed inputs; they do not authenticate an approver. The approval dictionary in the demo is a fixture, not a real user's permission.
- The regression suite checks a tiny deterministic formatter. It does not measure a language model's output quality or prove general improvement.
- Policy keys governing external actions are excluded from automatic proposals here. The example contains no outbound tools, autonomous self-editing, or model training.
- A production consumer must verify identity and authorization, write configuration atomically, monitor results, and provide rollback. This repository stops at a tested candidate and receipt.

The older system used local feedback files, private logs, and scheduled model-assisted review. This public edition replaces those inputs with fictional records and adds explicit version checks. It does not claim that the demo is the deployed system.

## Related work

[Agent OS](https://github.com/dyjhhh/agent-os) · [Evaluation gates](https://github.com/dyjhhh/agent-eval-gates) · [Reliability](https://github.com/dyjhhh/agent-reliability) · [Security hooks](https://github.com/dyjhhh/agent-security-hooks)

Built by Yujia Dong with Claude Code and Codex. The public extraction and tests were developed with Codex; design choices and review remain my responsibility.

MIT license. See [LICENSE](LICENSE).
