all: default

default: clean dev_deps pylint test

.venv:
	if [ ! -e ".venv/bin/activate_this.py" ] ; then virtualenv --clear .venv ; fi

dev_deps: .venv
	PYTHONPATH=$(PYTHONPATH):.venv ; . .venv/bin/activate && .venv/bin/pip install -U -r dev_requirements.txt

clean:
	find . -type f -name '*.pyc' -delete
	find . -type f -path '*/__pycache__/*' -delete
	find . -type d -empty -delete
	@rm -rf tmp_test/
	@rm -rf .venv/

test:
	PYTHONPATH=$(PYTHONPATH):.venv:. . .venv/bin/activate && python -W default setup.py nosetests --with-xunit --verbosity=2

pylint:
	PYTHONPATH=$(PYTHONPATH):.venv:. . .venv/bin/activate && python setup.py lint --lint-rcfile=.pylintrc --lint-reports=no --lint-packages=googleservices/

deploy:
	rm -rf dist/
	PYTHONPATH=$(PYTHONPATH):.venv:. . .venv/bin/activate && python setup.py sdist
	curl -F package=@dist/`ls -t1 dist/ | grep tar.gz | head -n1` $(FURY_API_URL)

