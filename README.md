# PyGoogleStorage
A python wrapper for Google's Shared utils for all services API calls

# Using

### As a git module

* Add repo as a submodule to your project
* symlink the *labgoo* subfolder to your a folder in your PYTHONPATH
* Import the module in your code:
```
import googleservices
```

### Using pip

Add to your requirements.txt:
```
git://git@github.com:Labgoo/PyGoogleServices.git
```

Import the module in your code:
```
import googleservices
```


# Contributing
All pull requests should pass the test suite and our pylint guidelines, which can be launched simply with:
```
$ make test
$ make pylint
```

Running test requires the unittest2 (standard in Python 2.7+) and mock libraries.
To install development dependencies run:
```
pip install -r dev_requirements.txt
```

In order to test coverage, please use:
```
make coverage
```

# Changelog
