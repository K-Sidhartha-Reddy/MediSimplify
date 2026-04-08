from transformers import T5Tokenizer, T5ForConditionalGeneration

# load trained model
model_path = "models/t5-medical-new"

tokenizer = T5Tokenizer.from_pretrained(model_path)
model = T5ForConditionalGeneration.from_pretrained(model_path)

# sample medical text
text = "simplify: Patient diagnosed with hypertension and prescribed beta blockers."

# tokenize
inputs = tokenizer(text, return_tensors="pt", truncation=True)

# generate output
outputs = model.generate(**inputs, max_length=100)

# decode
result = tokenizer.decode(outputs[0], skip_special_tokens=True)

print("\nOriginal:")
print(text)

print("\nSimplified:")
print(result)
