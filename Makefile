clean:
	find . -name "*.pyc" -delete
	find . -name ".DS_Store" -delete
	rm -rf *.egg
	rm -rf *.egg-info
	rm -rf __pycache__
	rm -rf build
	rm -rf dist


test:
	python test_leadbutt.py


# Release Instructions:
#
# 1. bump version number
# 2. `git commit "bump version to v<version>"`
# 3. `git tag v<version>`
# 4. `make build`
#
# If this doesn't work, make sure you have wheels installed:
#     pip install wheel
.PHONY: build
build:
	python setup.py sdist bdist_wheel upload


# makes it easier to test setup.py's entry points
reinstall:
	pip uninstall cloudwatch-to-graphite --yes
	pip install .
