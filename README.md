# Bad App

Remember to log your HTTP codes correctly! 😊

A sample Flask application that implements two endpoints:

- `/`: A simple Hello World endpoint which returns an HTTP 200 as expected
- `/error`: An endpoint with logic errors and incorrect logging of HTTP error codes, resulting in HTTP 200 even in the event of an error

This is a demonstration of how HTTP error codes can incorrectly be implemented in an application, which can mask errors and hide issues in observability tools.

Incorrect HTTP 200 returned (implemented in this app):
```
@app.route("/error", methods=["GET"])
def error():
    try:
        val1 = "string"
        val2 = 100
        final_val = val1 + val2 # This will fail -- you can't concatenate a string with an integer!
        return final_val
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}) # This should return an HTTP 500 as there was an error; but instead will return with HTTP 200!
```

Correct HTTP 500 returned:
```
@app.route("/error", methods=["GET"])
def error():
    try:
        val1 = "string"
        val2 = 100
        final_val = val1 + val2 # This will fail -- you can't concatenate a string with an integer!
        return final_val
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500 # This now correctly returns HTTP 500!
```

Alternatively, you can use Flask's built-in abort method like `abort(500)` to throw the proper status code.

### Setup

Local:
```
pip install pipenv
pipenv install && pipenv shell
pipenv run python main.py
```

Docker:
```
docker run -d -p 5000:5000 jonfairbanks/bad-app
```