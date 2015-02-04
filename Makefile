test:
	nosetests ./code/googleservices/tests/* -x --processes=20 --process-timeout 800 --with-xunitmp --nologcapture
test_with_cov:
	nosetests ./code/googleservices/tests/* --processes=20 --process-timeout 800 --with-xunitmp --with-cov --cov-config nose-cov.config --cov-report xml --nologcapture --logging-level=WARNING

lint:
	pylint -f colorized --rcfile=.pylintrc ./code/googleservices/  || exit 0
