VERSION=0.4.0


help:
	@echo "make commands:"
	@echo "  make help    - this help"
	@echo "  make clean   - remove temporary files"
	@echo "  make test    - run test suite"
	@echo "  make install - install this package"
	@echo "  make release - prep a release and upload to PyPI"


clean:
	find . -name "*.pyc" -delete
	find . -name ".DS_Store" -delete
	rm -rf *.egg
	rm -rf *.egg-info
	rm -rf __pycache__
	rm -rf build
	rm -rf dist


test:
	python -m unittest discover


# Release Instructions:
#
# 1. bump version number above
# 4. `make release`
#
# If this doesn't work, make sure you have wheels installed:
#     pip install wheel
release:
	@sed -i -r /version/s/[0-9.]+/$(VERSION)/ setup.py
	@sed -i -r /__version__/s/[0-9.]+/$(VERSION)/ leadbutt.py
	@sed -i -r /__version__/s/[0-9.]+/$(VERSION)/ plumbum.py
	@git commit -am "bump version to v$(VERSION)"
	@git tag v$(VERSION)
	python setup.py sdist bdist_wheel upload


# makes it easier to test setup.py's entry points
install:
	-pip uninstall cloudwatch-to-graphite --yes
	pip install .
