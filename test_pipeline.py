from transformers import T5Tokenizer, T5ForConditionalGeneration
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# ── 1. Load T5 Simplification Model ───────────────────────
print("Loading T5 model...")
t5_tokenizer = T5Tokenizer.from_pretrained("/Users/ksidharthareddy/medicalreportssimplifier/models/t5-medical")
t5_model = T5ForConditionalGeneration.from_pretrained("/Users/ksidharthareddy/medicalreportssimplifier/models/t5-medical")

# ── 2. Load BioBERT Classifier ────────────────────────────
print("Loading BioBERT model...")
bert_tokenizer = AutoTokenizer.from_pretrained("/Users/ksidharthareddy/medicalreportssimplifier/models/biobert-condition")
bert_model = AutoModelForSequenceClassification.from_pretrained("/Users/ksidharthareddy/medicalreportssimplifier/models/biobert-condition")

labels = ["Birth Control", "Depression", "Diabetes", "High Blood Pressure", "Pain"]

# ── 3. Test Simplification ────────────────────────────────
def simplify(text):
    input_text = "simplify for patient: " + text
    inputs = t5_tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
    outputs = t5_model.generate(inputs["input_ids"], max_length=128)
    return t5_tokenizer.decode(outputs[0], skip_special_tokens=True)

# ── 4. Test Classification ────────────────────────────────
def classify(text):
    inputs = bert_tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        outputs = bert_model(**inputs)
    pred = torch.argmax(outputs.logits, dim=1).item()
    return labels[pred]

# ── 5. Run Test ───────────────────────────────────────────
test_text = "Patient has persistent hypertension with elevated blood pressure readings of 160/100 mmHg"

print("\n--- TEST RESULTS ---")
print("Original:", test_text)
print("Simplified:", simplify(test_text))
print("Condition:", classify(test_text))