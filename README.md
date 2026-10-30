# API de extração de dados

API em FastAPI que recebe um texto e devolve um JSON com os campos extraídos.

| Rota | O que extrai |
|---|---|
| `POST /extract/invoice` | número, data, fornecedor, itens e total de uma nota fiscal |
| `POST /extract/resume` | nome, e-mail, anos de experiência, empresa atual e skills de um currículo |
| `POST /extract/ticket` | categoria, prioridade, sentimento e resumo de um e-mail de suporte |
| `GET /health` | status |

Os campos de cada rota estão em `extractor_api/schemas.py` (modelos Pydantic), e o Claude é obrigado a devolver nesse formato.

## Como rodar

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
uvicorn extractor_api.main:app --reload     # docs em http://localhost:8000/docs
python evaluate.py                          # mede acerto por campo em data/labeled.json
python -m pytest tests
```

Também tem Dockerfile:

```bash
docker build -t extractor-api .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY extractor-api
```

## Observações

- Se o dado não está no texto, o campo volta `null` (o prompt pede para não inventar).
- Erros da API de IA viram códigos HTTP: recusa = 422, limite de uso = 429, falha do provedor = 502.
- O `data/labeled.json` tem 6 exemplos que eu rotulei e serve de ponto de partida para o `evaluate.py`.

## Próximos passos

- Aumentar o `labeled.json` e registrar aqui a acurácia por campo
- Processar vários documentos de uma vez
- Adicionar autenticação por chave na API
