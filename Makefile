.PHONY: install run tests clean

VENV_DIR = venv

install: $(VENV_DIR)/bin/activate
	$(VENV_DIR)/bin/pip install -r requirements.txt

$(VENV_DIR)/bin/activate:
	python -m venv $(VENV_DIR)
	@echo "Virtual environment created. Activate it with: source $(VENV_DIR)/bin/activate"

run: install
	PYTHONPATH=src $(VENV_DIR)/bin/python -m uvicorn src.main:app --host 0.0.0.0

tests:
	PYTHONPATH=src $(VENV_DIR)/bin/python -m unittest discover tests/unit
	PYTHONPATH=src $(VENV_DIR)/bin/python -m unittest discover tests/integration

clean:
	rm -rf $(VENV_DIR)
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '.pytest_cache' -exec rm -rf {} +
	find . -name '*.pyc' -exec rm -f {} +
	@echo "Cleaned up! check if you have the virtual environment still activate!"
