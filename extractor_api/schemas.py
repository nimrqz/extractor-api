from typing import Literal

from pydantic import BaseModel, Field

class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float

class Invoice(BaseModel):
    invoice_number: str
    issue_date: str = Field(description="Data de emissão no formato YYYY-MM-DD")
    supplier_name: str
    supplier_tax_id: str | None = Field(description="CNPJ/CPF/Tax ID, se houver")
    currency: str = Field(description="Código ISO 4217, ex.: BRL, USD")
    items: list[LineItem]
    total: float

class Resume(BaseModel):
    name: str
    email: str | None
    location: str | None
    years_experience: int | None = Field(description="Anos de experiência profissional total")
    current_company: str | None
    skills: list[str]

class Ticket(BaseModel):
    category: Literal["incident", "billing", "feature_request", "question", "other"]
    priority: Literal["low", "medium", "high"]
    sentiment: Literal["positive", "neutral", "negative"]
    summary: str = Field(description="Resumo em uma frase")
    action_items: list[str]

SCHEMAS: dict[str, type[BaseModel]] = {"invoice": Invoice, "resume": Resume, "ticket": Ticket}
