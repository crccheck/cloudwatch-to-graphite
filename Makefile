VERSION=0.8.0


help:
	@echo "help"
	@echo "-------------------------------------------------------"
	@echo "make help     this help"
	@echo "make clean    remove temporary files"
	@echo "make test     run test suite"
	@echo "make install  install this package locally"
	@echo "make release  prep a release and upload to PyPI"


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

version:
	@sed -i -r /version/s/[0-9.]+/$(VERSION)/ setup.py
	@sed -i -r /__version__/s/[0-9.]+/$(VERSION)/ leadbutt.py
	@sed -i -r /__version__/s/[0-9.]+/$(VERSION)/ plumbum.py

# Release instructions
# 1. bump VERSION above
# 2. run `make release`
# 3. `git push --tags origin master`
# 4. update release notes
release: clean version
	@-git commit -am "bump version to v$(VERSION)"
	@-git tag $(VERSION)
	@-pip install wheel > /dev/null
	python setup.py sdist bdist_wheel upload

# makes it easier to test setup.py's entry points
install:
	-pip uninstall cloudwatch-to-graphite --yes
	pip install .
