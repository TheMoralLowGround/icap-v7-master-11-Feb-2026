import Levenshtein
from flask import jsonify, request


def init(app):
    @app.route("/aidbsemeng", methods=["POST", "GET"])
    def aidbsemeng():
        try:
            print("Processing Request")
            data = request.get_json()
            function_name = data["function"]
            arguments = data["arguments"]

            function = getattr(Levenshtein, function_name)
            result = function(*arguments)

            response = {"data": result}
            return jsonify(response)
        except Exception as error:
            response = {"error": str(error)}
            return jsonify(response), 400
