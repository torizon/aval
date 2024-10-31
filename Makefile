BLACK = black
FLAKE8 = flake8

.PHONY: check_black
check_black:
	@if ! command -v $(BLACK) >/dev/null 2>&1; then \
		echo "Error: black is not installed. Please install it by running 'pip install black'."; \
		exit 1; \
	fi

.PHONY: check_flake8
check_flake8:
	@if ! command -v $(FLAKE8) >/dev/null 2>&1; then \
		echo "Error: flake8 is not installed. Please install it by running 'pip install flake8'."; \
		exit 1; \
	fi

.PHONY: lint
lint: check_flake8
	$(FLAKE8) --ignore=E501,W503

.PHONY: format
format: check_black
	$(BLACK) --verbose --line-length 80 -- *.py

.PHONY: lintmat
lintmat: format lint

.PHONY: install
install:
	pip install -r requirements.txt

.PHONY: test
test:
	coverage run -m unittest discover -v -s . -p 'test_*.py'
