import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# ── 1. Load ONLY 5000 samples (instead of 160k) ───────────
df = pd.read_csv("frontend/components/data/drugsComTrain_raw.csv").dropna()
df = df[["review", "condition"]].dropna()
df.columns = ["text", "label"]

# Top 5 conditions only (instead of 10)
top_conditions = df["label"].value_counts().head(5).index
df = df[df["label"].isin(top_conditions)]

# Use only 5000 samples
df = df.sample(n=5000, random_state=42)

le = LabelEncoder()
df["label"] = le.fit_transform(df["label"])
num_labels = len(le.classes_)
print("Labels:", le.classes_)
print("Total samples:", len(df))

# ── 2. Split ──────────────────────────────────────────────
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

# ── 3. Tokenize ───────────────────────────────────────────
tokenizer = AutoTokenizer.from_pretrained("dmis-lab/biobert-base-cased-v1.2")

def tokenize(batch):
    return tokenizer(
        batch["text"],
        truncation=True,
        padding="max_length",
        max_length=128  # reduced from 256
    )

train_dataset = Dataset.from_pandas(train_df).map(tokenize, batched=True)
test_dataset  = Dataset.from_pandas(test_df).map(tokenize, batched=True)

train_dataset = train_dataset.rename_column("label", "labels")
test_dataset  = test_dataset.rename_column("label", "labels")

train_dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])
test_dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

# ── 4. Model ──────────────────────────────────────────────
model = AutoModelForSequenceClassification.from_pretrained(
    "dmis-lab/biobert-base-cased-v1.2",
    num_labels=num_labels
)

# ── 5. Training Args (FASTER) ─────────────────────────────
training_args = TrainingArguments(
    output_dir="./models/biobert-condition",
    num_train_epochs=1,        # reduced from 2
    per_device_train_batch_size=16,  # increased from 8
    per_device_eval_batch_size=16,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    logging_steps=50,
    load_best_model_at_end=True,
    fp16=False
)

# ── 6. Train ──────────────────────────────────────────────
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset
)

print("Starting BioBERT training...")
trainer.train()

# ── 7. Save ───────────────────────────────────────────────
model.save_pretrained("./models/biobert-condition")
tokenizer.save_pretrained("./models/biobert-condition")
print("BioBERT model saved!")