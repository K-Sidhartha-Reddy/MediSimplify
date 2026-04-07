import pandas as pd
import json
from transformers import (
    T5ForConditionalGeneration,
    T5Tokenizer,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    DataCollatorForSeq2Seq,
)
from datasets import Dataset
from sklearn.model_selection import train_test_split

print("Loading datasets...")

# ── 1. Load Synthetic Dataset ──────────────────────────────
with open("data/synthetic_medical_data.json", "r") as f:
    synthetic_data = json.load(f)

synthetic_df = pd.DataFrame(synthetic_data)
print(f"Synthetic pairs: {len(synthetic_df)}")

# ── 2. Load Kaggle mtsamples Dataset ──────────────────────
kaggle_df = pd.read_csv(
    "frontend/components/data/mtsamples.csv"
).dropna(subset=["transcription", "description"])

kaggle_df = kaggle_df[["transcription", "description"]]
kaggle_df.columns = ["input", "output"]
kaggle_df["input"] = "simplify for patient: " + kaggle_df["input"].str[:400]
kaggle_df["output"] = kaggle_df["output"].str[:200]
kaggle_df = kaggle_df.sample(n=min(200, len(kaggle_df)), random_state=42)
print(f"Kaggle pairs: {len(kaggle_df)}")

# ── 3. Combine Both Datasets ──────────────────────────────
combined_df = pd.concat([synthetic_df, kaggle_df], ignore_index=True)
combined_df = combined_df.dropna()
combined_df = combined_df.sample(frac=1, random_state=42).reset_index(drop=True)
print(f"Total combined pairs: {len(combined_df)}")

# ── 4. Tokenize ───────────────────────────────────────────
print("Loading T5-base tokenizer...")
tokenizer = T5Tokenizer.from_pretrained("t5-base")

def tokenize(batch):
    model_inputs = tokenizer(
        batch["input"],
        max_length=512,
        truncation=True,
        padding="max_length"
    )
    labels = tokenizer(
        batch["output"],
        max_length=256,
        truncation=True,
        padding="max_length"
    )
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

dataset = Dataset.from_pandas(combined_df)
tokenized = dataset.map(tokenize, batched=True)
print("Tokenization complete!")

# ── 5. Load T5-base Model ─────────────────────────────────
print("Loading T5-base model...")
model = T5ForConditionalGeneration.from_pretrained("t5-base")
data_collator = DataCollatorForSeq2Seq(tokenizer, model=model, padding=True)

# ── 6. Training Arguments ─────────────────────────────────
training_args = Seq2SeqTrainingArguments(
    output_dir="./models/t5-medical-v2",
    num_train_epochs=30,
    per_device_train_batch_size=4,
    learning_rate=3e-4,
    warmup_steps=100,
    logging_steps=50,
    save_steps=500,
    predict_with_generate=True,
    fp16=False,
    generation_max_length=256,
)

# ── 7. Train ──────────────────────────────────────────────
trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    data_collator=data_collator,
    tokenizer=tokenizer,
)

print(f"\nStarting training with {len(combined_df)} pairs...")
print("This will take 20-30 minutes...\n")
trainer.train()

# ── 8. Save ───────────────────────────────────────────────
model.save_pretrained("./models/t5-medical-v2")
tokenizer.save_pretrained("./models/t5-medical-v2")
print("\n✅ Model saved to ./models/t5-medical-v2")

# ── 9. Quick Test ─────────────────────────────────────────
print("\n--- TESTING MODEL ---")
test_input = "simplify for patient: Patient Name Rahul Sharma Age 32 Diagnosis mild viral fever headache body pain Prescription Tab Paracetamol 500 mg 1 tablet three times daily after food 5 days Cap Amoxicillin 250 mg 1 capsule twice daily after food 7 days Tab Cetirizine 10 mg 1 tablet at night 5 days"

inputs = tokenizer(test_input, return_tensors="pt", max_length=512, truncation=True)
outputs = model.generate(
    inputs["input_ids"],
    max_length=256,
    num_beams=4,
    early_stopping=True
)
result = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(f"Input: {test_input[:100]}...")
print(f"Output: {result}")
print("\n✅ Training complete! Update simplify.py to use models/t5-medical-v2")
