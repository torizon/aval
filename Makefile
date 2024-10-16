BLACK = black

.PHONY: check_black
check_black:
	@if ! command -v $(BLACK) >/dev/null 2>&1; then \
		echo "Error: black is not installed. Please install it by running 'pip install black'."; \
		exit 1; \
	fi

.PHONY: format
format: check_black
	$(BLACK) --verbose --line-length 80 -- *.py

.PHONY: install
install:
	pip install -r requirements.txt

.PHONY: test
test:
	coverage run -m unittest discover -v -s . -p 'test_*.py'
