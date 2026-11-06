.PHONY: dev test backend-test

dev:
	./scripts/dev.sh

backend-test:
	cd backend && .venv/bin/python -m pytest

test:
	./scripts/test.sh
