.PHONY: db-up db-down db-seed redis-up compose-up compose-down compose-logs backend-install verify-phase2 verify-phase3 verify-phase4 verify-phase5 verify-phase6 verify-phase7 verify-phase8 verify-phase9 verify-phase10

db-up:
	docker compose up -d postgres redis

redis-up:
	docker compose up -d redis

db-down:
	docker compose down

compose-up:
	docker compose up --build

compose-up-d:
	docker compose up --build -d

compose-down:
	docker compose down

compose-logs:
	docker compose logs -f

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

verify-phase8:
	cd frontend && npm run test && npm run build

verify-phase9:
	backend/.venv/bin/python backend/scripts/verify_phase9.py

verify-phase10:
	backend/.venv/bin/python backend/scripts/verify_phase10.py
