from transformers import pipeline
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
MODEL_PATH = BASE_DIR / "models" / "t5-medical-new"

print(f"Loading simplification model from: {MODEL_PATH}")

simplifier = pipeline(
    "summarization",
    model=str(MODEL_PATH),
    max_length=200,
    min_length=50
)

print("Model loaded!")

def simplify_text(text: str) -> str:
    # Create a patient-friendly prompt
    prompt = f"""Convert this medical report to simple language a patient can understand. 
    Replace medical terms with everyday words:
    {text[:800]}"""
    
    result = simplifier(
        prompt,
        max_length=300,
        min_length=50,
        do_sample=False
    )
    
    simplified = result[0]["summary_text"]
    
    # Add plain language replacements
    replacements = {
        "Tab.": "Tablet",
        "Cap.": "Capsule",
        "mg": "milligrams",
        "Paracetamol": "Paracetamol (pain and fever reliever)",
        "Amoxicillin": "Amoxicillin (antibiotic)",
        "Cetirizine": "Cetirizine (allergy medicine)",
        "viral fever": "infection caused by a virus",
        "diagnosis": "what the doctor found",
        "prescription": "medicines prescribed",
        "dosage": "how much to take",
    }
    
    for medical, plain in replacements.items():
        simplified = simplified.replace(medical, plain)
    
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