from functools import lru_cache
from typing import Literal

import anthropic
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .extractor import ExtractionError, extract
from .schemas import SCHEMAS, Invoice, Resume, Ticket

app = FastAPI(
    title="Extractor API",
    description="Transforma texto não estruturado (notas, currículos, e-mails) em JSON validado.",
    version="1.0.0",
)

class ExtractRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50_000, description="Texto bruto do documento")

@lru_cache
def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic()

def run(kind: str, body: ExtractRequest, client: anthropic.Anthropic):
    try:
        return extract(client, SCHEMAS[kind], body.text)
    except ExtractionError as exc:
        raise HTTPException(422, str(exc)) from exc
    except anthropic.RateLimitError as exc:
        raise HTTPException(429, "Limite de requisições do provedor atingido") from exc
    except anthropic.APIConnectionError as exc:
        raise HTTPException(503, "Falha de conexão com o provedor de IA") from exc
    except anthropic.APIStatusError as exc:
        raise HTTPException(502, f"Erro do provedor de IA ({exc.status_code})") from exc

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "kinds": sorted(SCHEMAS)}

@app.post("/extract/invoice", response_model=Invoice)
def extract_invoice(body: ExtractRequest, client=Depends(get_client)):
    return run("invoice", body, client)

@app.post("/extract/resume", response_model=Resume)
def extract_resume(body: ExtractRequest, client=Depends(get_client)):
    return run("resume", body, client)

@app.post("/extract/ticket", response_model=Ticket)
def extract_ticket(body: ExtractRequest, client=Depends(get_client)):
    return run("ticket", body, client)
