# Variables
PYTHON = python3
SCRIPT = Processing_Data.py
MODEL_SCRIPT = Model.py
VENV_DIR = venv
WEB_DIR = Web  # Directory containing app.py and HTML files

# Targets
default: install process_data run_model

# Create and activate the virtual environment, install dependencies
install:
	$(PYTHON) -m venv $(VENV_DIR)
	./$(VENV_DIR)/bin/pip install --upgrade pip
	./$(VENV_DIR)/bin/pip install -r requirements.txt

# Run the data processing script in the virtual environment
process_data:
	@echo "Running the full data processing pipeline in virtual environment..."
	./$(VENV_DIR)/bin/python $(SCRIPT)

# Run the model script in the virtual environment
run_model:
	@echo "Running the model script in virtual environment..."
	./$(VENV_DIR)/bin/python $(MODEL_SCRIPT)
run_website:
	@echo "Running the website..."
	cd $(WEB_DIR) && ../$(VENV_DIR)/bin/flask run --host=0.0.0.0 --port=3000

# Clean up: remove intermediate and output files
clean_Data:
	@echo "Cleaning up intermediate and output folders..."
	rm -rf CSV_version_WaveData MergedData CleanedData
	rm -rf $(VENV_DIR)
	@echo "All temporary and output files removed."
