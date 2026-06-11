.PHONY: db-up db-down db-seed redis-up backend-install verify-phase2 verify-phase3 verify-phase4 verify-phase5 verify-phase6 verify-phase7

db-up:
	docker compose up -d postgres redis

redis-up:
	docker compose up -d redis

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

verify-phase5:
	backend/.venv/bin/python backend/scripts/verify_phase5.py

verify-phase6:
	backend/.venv/bin/python backend/scripts/verify_phase6.py

verify-phase7:
	backend/.venv/bin/python backend/scripts/verify_phase7.py
