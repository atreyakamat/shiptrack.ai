from flask import Blueprint, jsonify, request

from .store import store

api = Blueprint("api", __name__)


@api.get("/health")
def health() -> tuple[dict, int]:
    return {"status": "ok"}, 200


@api.get("/shipments")
def list_shipments():
    shipments = [shipment.to_dict() for shipment in store.list_shipments()]
    return jsonify(shipments), 200


@api.post("/shipments")
def create_shipment():
    payload = request.get_json(silent=True) or {}
    try:
        shipment = store.add_shipment(payload)
    except ValueError as error:
        return {"error": str(error)}, 400
    return jsonify(shipment.to_dict()), 201


@api.get("/shipments/<shipment_id>")
def get_shipment(shipment_id: str):
    shipment = store.get_shipment(shipment_id)
    if shipment is None:
        return {"error": "shipment not found"}, 404
    return jsonify(shipment.to_dict()), 200


@api.post("/shipments/<shipment_id>/refresh")
def refresh_shipment(shipment_id: str):
    shipment = store.refresh_shipment(shipment_id)
    if shipment is None:
        return {"error": "shipment not found"}, 404
    return jsonify(shipment.to_dict()), 200
