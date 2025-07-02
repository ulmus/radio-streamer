# Makefile for radio-streamer testing

.PHONY: test test-fast test-unit test-integration test-api test-coverage install-test-deps clean-test

# Install test dependencies
install-test-deps:
	python -m pip install -e .[test]

# Run all tests
test:
	python run_tests.py --all

# Run fast tests (no hardware, no slow tests)
test-fast:
	python run_tests.py --fast

# Run unit tests only
test-unit:
	python run_tests.py --unit

# Run integration tests only
test-integration:
	python run_tests.py --integration

# Run API tests only
test-api:
	python run_tests.py --api

# Run tests with coverage report
test-coverage:
	python run_tests.py --coverage

# Clean test artifacts
clean-test:
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -f .coverage
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

# Setup development environment
dev-setup: install-test-deps
	@echo "Development environment setup complete"
	@echo "Run 'make test' to run the test suite"

# CI/CD target
ci: install-test-deps test-coverage
	@echo "CI pipeline complete"
