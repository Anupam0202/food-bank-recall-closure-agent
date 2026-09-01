.PHONY: install dev live preview test pytest lint check smoke http-smoke seed adk-smoke live-smoke images docker deploy zip
install:
	python -m pip install -r requirements.txt

dev:
	AI_MODE=mock uvicorn app.main:app --reload --port 8080

live:
	AI_MODE=live uvicorn app.main:app --port 8080

preview:
	python scripts/offline_preview_server.py

test:
	python -m unittest discover -s tests -v

pytest:
	pytest -q

lint:
	ruff check .

check:
	python -m compileall -q app tests scripts
	python scripts/check_repo.py
	python -m unittest discover -s tests -v

smoke:
	AI_MODE=mock python scripts/run_golden_path.py

http-smoke:
	python scripts/http_smoke.py

seed:
	python scripts/seed_demo.py

adk-smoke:
	python scripts/adk_import_smoke.py

live-smoke:
	RUN_LIVE_GEMINI_TESTS=1 python scripts/live_gemini_smoke.py

images:
	python scripts/generate_fixture_images.py

docker:
	docker build -t recall-closure-agent:local .

deploy:
	bash infra/deploy_cloud_run.sh

zip:
	bash scripts/package_release.sh
