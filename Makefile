build:
	virtualenv .venv
	.venv/bin/pip3 install -e .
	.venv/bin/pip3 install -r requirements_dev.txt

format:
	.venv/bin/ruff format

clean:
	@rm -rf build .venv* .ruff_cache
	@find . -type f -name "*.py[co]" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -iname "*.egg-info" -exec rm -rf {} +
