from flask import jsonify, request
from postal.parser import parse_address


def init(app):
    @app.route("/parse_address", methods=["POST"])
    def postal_parse_address():
        data = request.get_json()
        address = data["address"]
        result = parse_address(address)
        response = {"data": result}
        return jsonify(response)

    @app.route("/parse_address_bulk", methods=["POST"])
    def postal_parse_address_bulk():
        data = request.get_json()
        address_inputs = data["address_inputs"]
        result_items = [parse_address(address) for address in address_inputs]
        response = {"data_items": result_items}
        return jsonify(response)
