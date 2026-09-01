# Architecture Decisions

| ID | Decision | Reason |
|---|---|---|
| ADR-001 | Use a Python modular monolith. | One deployable preserves transactional consistency and maximizes deadline reliability. |
| ADR-002 | Use one ADK 2.x `RecallCoordinatorAgent`. | One coordinator demonstrates meaningful tool use without an unnecessary agent swarm. |
| ADR-003 | Keep deterministic workflow/state machine authoritative. | Safety-sensitive writes and closure rules must be explicit and testable. |
| ADR-004 | Match deterministic identifiers before Gemini. | Stable UPC+lot evidence may create a reversible hold; interpretation alone cannot. |
| ADR-005 | Use Firestore for production state. | Serverless transactions fit incident/task documents and Pub/Sub redelivery. |
| ADR-006 | Use authenticated Pub/Sub push, not polling. | Push supports event-driven delivery, bounded retry, dead-letter handling, and scale-to-zero. |
| ADR-007 | Deploy one Cloud Run service. | Cloud Run provides a simple container target, request identity, structured logs, and scale limits. |
| ADR-008 | Use server-rendered Jinja instead of a separate SPA. | It removes a second build pipeline and keeps the operations demo reliable. |
| ADR-009 | Make `live`, `mock`, and `replay` explicit modes. | Judges and operators must never mistake fixture/replay output for a live model request. |
| ADR-010 | Implement confirmation in application state/UI. | ADK confirmation features are not the sole safety boundary; human actions remain durable domain records. |
| ADR-011 | Pin Google ADK 2.7.1 and Gen AI SDK 2.20.0. | These were the latest stable releases found on 2026-09-01; code uses only documented 2.x public imports. Runtime installation was blocked offline and is not claimed as tested. |
| ADR-012 | Preserve originals and normalize only for comparison. | Auditors need unmodified source and inventory evidence alongside deterministic decisions. |
| ADR-013 | Use synthetic demo data. | It is reproducible and avoids presenting an active real recall as a product claim. |
| ADR-014 | Permit public read-only judging only with app-authenticated mutations and OIDC Pub/Sub. | It balances judge access with mutation and event protection. |
| ADR-015 | Serve local evidence through an administrator-authenticated proxy. | A public static media mount would violate the private-evidence boundary. |
| ADR-016 | Pin FastAPI 0.139.2, Pydantic 2.13.4, Starlette 1.3.1, Uvicorn 0.51.0, and Google Auth 2.56.0 for ADK 2.7.1. | Google ADK 2.7.1 requires FastAPI >=0.133, Pydantic >=2.12, Starlette >=1.3.1, Uvicorn >=0.34, and Google Auth >=2.47; the earlier FastAPI 0.116.1 pin was resolver-incompatible. |
