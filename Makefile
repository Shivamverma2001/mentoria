.PHONY: db-up db-down db-seed backend-install verify-phase2 verify-phase3 verify-phase4

db-up:
	docker compose up -d postgres

db-down:
	docker compose down

db-seed:
	cd backend && .venv/bin/python -m app.scripts.seed

backend-install:
	cd backend && python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt

verify-phase2:
	backend/.venv/bin/python backend/scripts/verify_phase2.py

verify-phase3:
	backend/.venv/bin/python backend/scripts/verify_phase3.py

verify-phase4:
	backend/.venv/bin/python backend/scripts/verify_phase4.py
