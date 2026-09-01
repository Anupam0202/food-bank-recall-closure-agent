# Sources

Access date for all entries: **2026-09-01**.

| Source | URL | Used for | Important limitation |
|---|---|---|---|
| All Things Agentic Hackathon rules | https://allthingsagentichackathon.devpost.com/rules | Category and submission constraints | Event terms can change; confirm before submission. |
| Hackathon dates | https://allthingsagentichackathon.devpost.com/details/dates | Deadline planning | Calendar is authoritative over this repository. |
| Hackathon resources | https://allthingsagentichackathon.devpost.com/resources | Required Google technology framing | Resource links do not prove implementation. |
| Gemini API documentation | https://ai.google.dev/gemini-api/docs | Current Google Gen AI SDK concepts | Model/account availability varies. |
| Gemini 3.7 Flash | https://ai.google.dev/gemini-api/docs/models/gemini-3.7-flash | Configured default model | The build sandbox had no credentials, so no live request was claimed. |
| Structured outputs | https://ai.google.dev/gemini-api/docs/structured-output | Pydantic response schema and JSON MIME | Schema compliance still requires local validation. |
| Document processing | https://ai.google.dev/gemini-api/docs/document-processing | PDF multimodal input design | Upload safety and retention remain application duties. |
| Image understanding | https://ai.google.dev/gemini-api/docs/image-understanding | Package observation design | Image output is non-authoritative and always reviewed. |
| Google ADK | https://adk.dev/ | Agent, runner, and tool concepts | 2.x has breaking changes from older 1.x examples. |
| ADK Python repository | https://github.com/google/adk-python | Confirmed public `from google.adk import Agent`; current release line | Repository main may move beyond the pin. |
| ADK custom tools | https://google.github.io/adk-docs/tools-custom/ | Typed function-tool conventions | Tool exposure must remain explicitly allowlisted. |
| ADK sessions/state | https://google.github.io/adk-docs/sessions/state/ | In-memory runner session construction | In-memory sessions are not durable business state. |
| ADK Cloud Run deployment | https://google.github.io/adk-docs/deploy/cloud-run/ | Deployment compatibility | This repository deploys the combined FastAPI/ADK app. |
| Google ADK 2.7.1 release history | https://pypi.org/project/google-adk/ | Exact selected package pin | Package installation was blocked in the offline build environment. |
| Google ADK 2.7.1 package metadata | https://raw.githubusercontent.com/google/adk-python/v2.7.1/pyproject.toml | Verified direct dependency bounds, including FastAPI >=0.133, Pydantic >=2.12, Starlette >=1.3.1, and Google Auth >=2.47 | The tag is version-specific; main-branch requirements may differ. |
| Google ADK 2.7.1 Python 3.12 constraints | https://raw.githubusercontent.com/google/adk-python/v2.7.1/constraints-3.12.txt | Selected resolver-compatible FastAPI, Starlette, Pydantic, Uvicorn, and Google Auth pins | The upstream file includes all ADK extras; this project keeps only the compatibility-critical subset. |
| FastAPI 0.139.2 | https://pypi.org/project/fastapi/0.139.2/ | Compatible FastAPI pin selected by ADK's official Python 3.12 constraints | Future upgrades require repeating the ADK compatibility check. |
| Google Gen AI SDK 2.20.0 release | https://github.com/googleapis/python-genai/releases/tag/v2.20.0 | Exact selected SDK pin | Newer releases require a deliberate compatibility review. |
| Cloud Run ADK deployment | https://docs.cloud.google.com/run/docs/ai/build-and-deploy-ai-agents/deploy-adk-agent | Cloud service shape | Requires an authenticated Google Cloud project. |
| Pub/Sub with Cloud Run | https://docs.cloud.google.com/run/docs/tutorials/pubsub | Authenticated push topology | Delivery is at least once; duplicates remain possible. |
| Pub/Sub subscription overview | https://docs.cloud.google.com/pubsub/docs/subscription-overview | Delivery and acknowledgement behavior | Exactly-once is not claimed for push delivery. |
| Pub/Sub dead-letter topics | https://docs.cloud.google.com/pubsub/docs/dead-letter-topics | Five-attempt DLQ setup | Forwarding is best-effort and requires service-agent IAM. |
| Firestore transactions | https://docs.cloud.google.com/firestore/native/docs/manage-data/transactions | Idempotent incident reservation | Transactions can retry; transaction functions must be safe. |
| Cloud Run secrets | https://docs.cloud.google.com/run/docs/configuring/services/secrets | Secret Manager references | Access still requires least-privilege IAM. |
| openFDA food enforcement API | https://open.fda.gov/apis/food/enforcement | Optional operator import fields | Not an authoritative public-alert or official lifecycle feed. |
| openFDA searchable fields | https://open.fda.gov/apis/food/enforcement/searchable-fields/ | Recall-number query and field mapping | Returned records can be incomplete or delayed. |
| FDA recalls and alerts | https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts | Official-notice handoff | Operators must use the current official page, not this app, for regulator guidance. |
| USDA FSIS recalls | https://www.fsis.usda.gov/recalls | Official meat/poultry/egg recall handoff | Not integrated automatically in this prototype. |

| Google Cloud Free Program | https://docs.cloud.google.com/free/docs/free-cloud-features | Billing requirement and monthly free allowances | Free Tier is an allowance; paid billing accounts can incur overages. |
| Cloud Run pricing | https://cloud.google.com/run/pricing | Request-based compute and request allowance | Region and traffic affect charges. |
| Cloud Run billing settings | https://docs.cloud.google.com/run/docs/configuring/billing-settings | CPU-throttled request-based billing | CLI flags can change; verify before deployment. |
| Cloud Run maximum instances | https://docs.cloud.google.com/run/docs/configuring/max-instances | One-instance demo cost guard | A service-level max is not an absolute budget cap. |
| Firestore pricing | https://cloud.google.com/firestore/pricing | One free database and operation/storage allowances | Backups, PITR, TTL, restores, and clones are not free. |
| Cloud Storage pricing | https://cloud.google.com/storage/pricing | Regional 5 GB-month allowance | Allowance is limited to eligible US regions. |
| Pub/Sub pricing | https://cloud.google.com/pubsub/pricing | Message-throughput allowance | Network and other service charges can still apply. |
| Secret Manager pricing | https://cloud.google.com/secret-manager/pricing | Active-version and access-operation allowance | Rotation and replication can add usage. |
| Cloud Billing budgets | https://cloud.google.com/billing/docs/how-to/budgets | Alert setup and limitations | Budgets notify; they do not automatically stop spending. |
| Gemini API pricing | https://ai.google.dev/gemini-api/docs/pricing | Developer API free/paid tier distinction | Model eligibility, rate limits, and data-use terms can change. |
| Gemini API keys | https://ai.google.dev/gemini-api/docs/api-key | AI Studio key creation and protection | API keys are secrets and must remain server-side. |
| FDA recall guidance | https://www.fda.gov/media/79108/download | Inventory examination, quarantine, downstream notification, response checks | Guidance does not replace current regulator instructions. |
| FSMA food traceability rule | https://www.fda.gov/food/food-safety-modernization-act-fsma/fsma-final-rule-requirements-additional-traceability-records-certain-foods | Critical tracking events, key data elements, and 24-hour records | Applicability and compliance dates require legal review. |
| GS1 Global Traceability Standard | https://www.gs1.org/standards/gs1-global-traceability-standard/current-standard | GTIN and lot/batch traceability framing | This prototype does not claim certified GS1/EPCIS interoperability. |
