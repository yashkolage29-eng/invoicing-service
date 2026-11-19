"""HTTP routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from . import repository
from .db import get_db
from .validation import ValidationError, parse_invoice

bp = Blueprint("invoices", __name__)


@bp.errorhandler(ValidationError)
def _validation_error(exc: ValidationError):
    return jsonify({"error": "validation_failed", "fields": exc.errors}), 422


@bp.errorhandler(repository.NotFoundError)
def _not_found(_exc: repository.NotFoundError):
    return jsonify({"error": "not_found"}), 404


@bp.errorhandler(repository.InvalidTransitionError)
def _conflict(exc: repository.InvalidTransitionError):
    return jsonify({"error": "invalid_transition", "detail": str(exc)}), 409


@bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@bp.post("/invoices")
def create_invoice():
    payload = parse_invoice(request.get_json(silent=True))
    invoice_id = repository.create_invoice(get_db(), payload)
    invoice = repository.get_invoice(get_db(), invoice_id)
    return jsonify(invoice), 201, {"Location": f"/invoices/{invoice_id}"}


@bp.get("/invoices")
def list_invoices():
    limit = request.args.get("limit", default=20, type=int)
    offset = request.args.get("offset", default=0, type=int)
    if not 1 <= limit <= 100 or offset < 0:
        raise ValidationError({"limit": "must be 1-100", "offset": "must be >= 0"})
    return jsonify(repository.list_invoices(get_db(), limit, offset))


@bp.get("/invoices/<int:invoice_id>")
def get_invoice(invoice_id: int):
    return jsonify(repository.get_invoice(get_db(), invoice_id))


@bp.post("/invoices/<int:invoice_id>/status")
def update_status(invoice_id: int):
    body = request.get_json(silent=True)
    status = body.get("status") if isinstance(body, dict) else None
    if not isinstance(status, str):
        raise ValidationError({"status": "required"})
    return jsonify(repository.set_status(get_db(), invoice_id, status))


@bp.delete("/invoices/<int:invoice_id>")
def delete_invoice(invoice_id: int):
    repository.delete_draft(get_db(), invoice_id)
    return "", 204
