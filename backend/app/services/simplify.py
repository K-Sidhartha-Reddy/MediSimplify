import re
from functools import lru_cache

from transformers import pipeline
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
MODEL_PATH = BASE_DIR / "models" / "t5-medical-new"


@lru_cache(maxsize=1)
def _load_simplifier():
    print(f"Loading simplification model from: {MODEL_PATH}")
    model = pipeline(
        "summarization",
        model=str(MODEL_PATH),
        max_length=200,
        min_length=50
    )
    print("Model loaded!")
    return model


def _fallback_simplify(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return "No readable medical text was provided."

    replacements = {
        r"\bTab\.\b": "Tablet",
        r"\bCap\.\b": "Capsule",
        r"\bmg\b": "milligrams",
        r"\bParacetamol\b": "Paracetamol (pain and fever reliever)",
        r"\bAmoxicillin\b": "Amoxicillin (antibiotic)",
        r"\bCetirizine\b": "Cetirizine (allergy medicine)",
        r"\bviral fever\b": "infection caused by a virus",
        r"\bdiagnosis\b": "what the doctor found",
        r"\bprescription\b": "medicines prescribed",
        r"\bdosage\b": "how much to take",
    }

    simplified = cleaned
    for pattern, replacement in replacements.items():
        simplified = re.sub(pattern, replacement, simplified, flags=re.IGNORECASE)

    return simplified

def simplify_text(text: str) -> str:
    cleaned_text = re.sub(r"\s+", " ", text).strip()
    if not cleaned_text:
        return "No readable medical text was provided."

    prompt = f"""Convert this medical report to simple language a patient can understand.
    Replace medical terms with everyday words:
    {cleaned_text[:800]}"""

    try:
        simplifier = _load_simplifier()
        result = simplifier(
            prompt,
            max_length=300,
            min_length=50,
            do_sample=False
        )
        simplified = result[0].get("summary_text", "").strip()
        if not simplified:
            return _fallback_simplify(cleaned_text)
    except Exception:
        return _fallback_simplify(cleaned_text)

    simplified = _fallback_simplify(simplified)
    return simplified

def extract_important_terms(text: str) -> list:
    medical_terms = [
        "hypertension", "diabetes", "fever", "infection",
        "blood pressure", "glucose", "cholesterol", "anemia",
        "cardiac", "renal", "hepatic", "pulmonary",
        "paracetamol", "amoxicillin", "cetirizine"
    ]
    found = []
    text_lower = text.lower()
    for term in medical_terms:
        if term in text_lower:
            found.append(term)
    return found