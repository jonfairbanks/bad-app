import logging

from flask import Flask, jsonify

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route("/")
def hello():
    logger.info("Hello World!")
    return "Hello World!"

@app.route("/error", methods=["GET"])
def error():
    try:
        val1 = "string"
        val2 = 100
        final_val = val1 + val2 # This will fail -- you can't concatenate a string with an integer!
        return final_val
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}) # This should return an HTTP 500; there was an error!

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0')