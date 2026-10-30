import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import anthropic
import httpx2 as httpx
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from evaluate import evaluate, score  # noqa: E402
from extractor_api.main import app, get_client  # noqa: E402
from extractor_api.schemas import Invoice, Ticket  # noqa: E402

class FakeClient:
    def __init__(self, parsed=None, error=None, stop_reason="end_turn"):
        self.parsed, self.error, self.stop_reason = parsed, error, stop_reason
        self.last = None
        self.messages = NS(parse=self._parse)

    def _parse(self, **kwargs):
        self.last = kwargs
        if self.error:
            raise self.error
        return NS(parsed_output=self.parsed, stop_reason=self.stop_reason)

def api_error(cls, status):
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return cls(message="x", response=httpx.Response(status, request=request), body=None)

INVOICE = Invoice(
    invoice_number="1", issue_date="2026-03-12", supplier_name="ACME", supplier_tax_id=None,
    currency="BRL", items=[], total=10.0,
)

def call(fake, path="/extract/invoice", text="nota"):
    app.dependency_overrides[get_client] = lambda: fake
    try:
        return TestClient(app).post(path, json={"text": text})
    finally:
        app.dependency_overrides.clear()

def test_health():
    assert TestClient(app).get("/health").json()["status"] == "ok"

def test_extract_invoice_ok_and_prompt_wraps_document():
    fake = FakeClient(INVOICE)
    r = call(fake)
    assert r.status_code == 200 and r.json()["total"] == 10.0
    assert fake.last["output_format"] is Invoice
    assert "<documento>" in fake.last["messages"][0]["content"]

def test_refusal_returns_422():
    assert call(FakeClient(None, stop_reason="refusal")).status_code == 422

@pytest.mark.parametrize("cls,status,expected", [
    (anthropic.RateLimitError, 429, 429),
    (anthropic.InternalServerError, 500, 502),
])
def test_provider_errors_are_mapped(cls, status, expected):
    assert call(FakeClient(error=api_error(cls, status))).status_code == expected

def test_empty_text_rejected_by_validation():
    assert call(FakeClient(INVOICE), text="").status_code == 422

def test_invalid_enum_in_ticket_schema():
    with pytest.raises(ValueError):
        Ticket(category="nope", priority="low", sentiment="neutral", summary="x", action_items=[])

def test_score_normalizes_case_and_floats():
    assert score({"name": " Ana ", "total": 10.001}, {"name": "ana", "total": 10.0}) == {
        "name": True, "total": True,
    }

def test_evaluate_aggregates_accuracy():
    cases = [{"kind": "invoice", "text": "x", "expected": {"invoice_number": "1", "total": 99.0}}]
    result = evaluate(FakeClient(INVOICE), cases)
    assert result["field_accuracy"] == 0.5
    assert result["by_field"]["invoice.invoice_number"] == 1.0
