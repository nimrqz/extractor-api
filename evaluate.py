import json
from collections import defaultdict
from pathlib import Path

import anthropic

from extractor_api.extractor import extract
from extractor_api.schemas import SCHEMAS

def norm(value):
    if isinstance(value, float):
        return round(value, 2)
    return str(value).strip().lower() if isinstance(value, str) else value

def score(predicted: dict, expected: dict) -> dict[str, bool]:
    return {field: norm(predicted.get(field)) == norm(want) for field, want in expected.items()}

def evaluate(client, cases: list[dict]) -> dict:
    per_field: dict[str, list[bool]] = defaultdict(list)
    for case in cases:
        predicted = extract(client, SCHEMAS[case["kind"]], case["text"]).model_dump()
        for field, ok in score(predicted, case["expected"]).items():
            per_field[f"{case['kind']}.{field}"].append(ok)
    total = [ok for results in per_field.values() for ok in results]
    return {
        "field_accuracy": sum(total) / len(total),
        "by_field": {k: sum(v) / len(v) for k, v in sorted(per_field.items())},
    }

if __name__ == "__main__":
    cases = json.loads((Path(__file__).parent / "data" / "labeled.json").read_text(encoding="utf-8"))
    print(json.dumps(evaluate(anthropic.Anthropic(), cases), indent=2, ensure_ascii=False))
