.PHONY: help
help: ## List and describe public targets
	@# Any targets with double-hashed comments will be treated as public, and those comments will be used as help text
	@grep -E '^[a-zA-Z_-]+:.*?##\s?.*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?##\s?"}; {printf "$(COLOR_HL)%-30s$(COLOR_RESET) %s\n", $$1, $$2}'


.PHONY: format
format: ## Automatically formats the Python code using ruff and gherkin
	ruff check --fix src/ tests/
	ruff format src/ tests/

.PHONY: lint
lint: ## Checks we've done a good job with our code.
	ruff check src/ tests/
	mypy --no-incremental src/
