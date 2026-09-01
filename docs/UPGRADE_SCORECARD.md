# Peak Upgrade Scorecard

The upgrade candidates were scored against the published hackathon weights: **Innovation & Operational Utility 40%**, **Architectural Discipline 30%**, and **Demo & Production Readiness 30%**. Scores are design judgments, not empirical market measurements.

| Candidate | Utility /40 | Architecture /30 | Demo /30 | Weighted total /100 | Decision |
|---|---:|---:|---:|---:|---|
| Tamper-evident closure evidence pack | 38 | 29 | 29 | **96** | Build |
| Redacted readiness control plane + free-tier guide | 34 | 29 | 30 | **93** | Build |
| Semantic HTTP smoke contract | 20 | 28 | 30 | **78** | Build as reliability prerequisite |
| Time-to-containment SLA dashboard | 31 | 22 | 24 | 77 | Defer until real timestamp/SLA policy exists |
| Barcode-camera scanning | 29 | 18 | 27 | 74 | Defer; browser/device risk distracts from closure proof |
| Automated openFDA polling | 28 | 21 | 20 | 69 | Defer; openFDA is weekly supporting data, not an authoritative alert feed |
| Multi-agent swarm | 18 | 15 | 22 | 55 | Reject; more failure surfaces without Taskmaster value |
| Generic chat assistant | 10 | 12 | 14 | 36 | Reject; conflicts with “complete workflow, not just a chatbot” |

## Selected ceiling architecture

1. **Keep one ADK coordinator.** The deterministic workflow remains the authority; the agent interprets and proposes.
2. **Add portable proof.** Each incident can produce a privacy-minimized ZIP with canonical records, per-file SHA-256 digests, and an ordered audit hash chain.
3. **Make readiness observable.** `/readiness` and `/api/readiness` disclose mode, cloud prerequisites, and cost guardrails without exposing secret values.
4. **Make setup truthful.** Local no-billing use and billing-required Google Cloud Free Tier use are documented as different paths.
5. **Test semantics, not marketing copy.** The real-server smoke test checks HTTP types, a stable application identifier, the dashboard heading, and redacted readiness JSON.

## Competitive position

Typical alert summarizers stop at detection; inventory tools stop at stock visibility; generic agent demos stop at text generation. This application differentiates on the complete operational chain:

**source provenance → schema-constrained interpretation → deterministic match authority → reversible hold/review → partner acknowledgement → closure blockers → tamper-evident evidence export**.

The design intentionally avoids fabricated integrations, unsafe disposition authority, unbounded autonomous writes, and an agent swarm that would weaken reliability.
