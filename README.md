# Bad App

A sample Flask application with two endpoints:

- `/`: A simple Hello World endpoint which returns an HTTP 200 as expected
- `/error`: An endpoint with logic errors and incorrect logging of HTTP error codes, resulting in HTTP 200 even in the event of an error

This is a demonstration of how HTTP error codes can incorrectly be implemented in an application, which can mask errors and hide issues in observability tools.

Remember to log your HTTP codes correctly! 😊

### Setup

```
pip install pipenv
pipenv install && pipenv shell
pipenv run python main.py
```