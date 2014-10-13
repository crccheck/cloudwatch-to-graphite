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


# If this doesn't work, make sure you have wheels installed:
#     pip install wheel
.PHONY: build
build:
	python setup.py sdist bdist_wheel upload
