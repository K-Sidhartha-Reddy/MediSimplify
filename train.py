import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import T5Tokenizer, T5ForConditionalGeneration, Trainer, TrainingArguments
from datasets import Dataset

# ── 1. Load Data ──────────────────────────────────────────
df = pd.read_csv("frontend/components/data/mtsamples.csv").dropna()
df = df[["transcription", "description"]]
df.columns = ["input_text", "target_text"]

# Add T5 prefix
df["input_text"] = "simplify for patient: " + df["input_text"].str[:512]
df["target_text"] = df["target_text"].str[:128]

# Train/test split
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

# ── 2. Load Tokenizer ──────────────────────────────────────
tokenizer = T5Tokenizer.from_pretrained("t5-small")

# ── 3. Tokenize ────────────────────────────────────────────
def tokenize(batch):
    inputs = tokenizer(
        batch["input_text"],
        max_length=512,
        truncation=True,
        padding="max_length"
    )
    targets = tokenizer(
        batch["target_text"],
        max_length=128,
        truncation=True,
        padding="max_length"
    )
    inputs["labels"] = targets["input_ids"]
    return inputs

train_dataset = Dataset.from_pandas(train_df).map(tokenize, batched=True)
test_dataset  = Dataset.from_pandas(test_df).map(tokenize, batched=True)

# ── 4. Training Arguments ──────────────────────────────────
training_args = TrainingArguments(
    output_dir="./models/t5-medical",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    logging_dir="./logs",
    logging_steps=50,
    load_best_model_at_end=True,
    fp16=False
)

# ── 5. Trainer ─────────────────────────────────────────────
model = T5ForConditionalGeneration.from_pretrained("t5-small")

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset
)

# ── 6. Train ───────────────────────────────────────────────
print("Starting training...")
trainer.train()

# ── 7. Save Model ──────────────────────────────────────────
model.save_pretrained("./models/t5-medical")
tokenizer.save_pretrained("./models/t5-medical")
print("Model saved to ./models/t5-medical")