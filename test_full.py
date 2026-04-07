import sys
sys.path.append('.')

# Direct simple test - no complex imports
from transformers import T5Tokenizer, T5ForConditionalGeneration

print("Loading T5 model...")
tokenizer = T5Tokenizer.from_pretrained("t5-small")
model = T5ForConditionalGeneration.from_pretrained(
    "./models/t5-medical/checkpoint-2340"
)

def simplify(text):
    input_text = "simplify for patient: " + text
    inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
    outputs = model.generate(inputs["input_ids"], max_length=128)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Test
test_text = "Patient has persistent hypertension with elevated blood pressure readings of 160/100 mmHg"
print("\n--- TEST RESULTS ---")
print("Original  :", test_text)
print("Simplified:", simplify(test_text))
print("\nPipeline working successfully!")