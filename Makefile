VERSION = $(shell cat VERSION)
ifeq ($(shell uname), Darwin)
	# Get this with: `brew install gnu-sed`
	SED = gsed
else
	SED = sed
endif

help: ## Shows this help
	@echo "$$(grep -h '#\{2\}' $(MAKEFILE_LIST) | sed 's/: #\{2\} /	/' | column -t -s '	')"


clean: ## Remove temporary files
	find . -name "*.pyc" -delete
	find . -name ".DS_Store" -delete
	rm -rf *.egg
	rm -rf *.egg-info
	rm -rf __pycache__
	rm -rf build
	rm -rf dist

test: ## Run test suite
	python -m unittest discover

.PHONY: version
version:
	@$(SED) -i -r /version/s/[0-9.]+/$(VERSION)/ setup.py
	@$(SED) -i -r /__version__/s/[0-9.]+/$(VERSION)/ leadbutt.py

# Release instructions
# 1. bump VERSION file
# 2. run `make release`
# 3. `git push --tags origin master`
# 4. update release notes
release: clean version
	@-git commit -am "bump version to v$(VERSION)"
	@-git tag $(VERSION)
	@-pip install wheel > /dev/null
	python setup.py sdist bdist_wheel upload

# makes it easier to test setup.py's entry points
install: ## Install this package locally
	-pip uninstall cloudwatch-to-graphite --yes
	pip install .
