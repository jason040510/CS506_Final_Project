# Define the virtual environment directory
VENV_DIR := venv

# Create and activate the virtual environment, install required dependencies
install:
	python3 -m venv $(VENV_DIR)                                        # Create the virtual environment
	./$(VENV_DIR)/bin/pip install --upgrade pip                        # Upgrade pip
	./$(VENV_DIR)/bin/pip install Flask                                # Ensure Flask is installed
	./$(VENV_DIR)/bin/pip install -r requirements.txt                  # Install other dependencies from requirements.txt

# Run the Flask application inside the virtual environment
run:
	./$(VENV_DIR)/bin/flask run --host=0.0.0.0 --port=3000             # Start Flask app

# Run tests using pytest
test:
	./$(VENV_DIR)/bin/pytest                                           # Run tests in the virtual environment

# Clean up: remove the virtual environment
clean:
	rm -rf $(VENV_DIR)                                                 # Delete the virtual environment
	find . -type f -name '*.pyc' -delete                               # Remove compiled Python files
	find . -type d -name '__pycache__' -delete                         # Remove __pycache__ directories