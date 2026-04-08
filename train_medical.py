import pandas as pd
from datasets import Dataset
from transformers import T5Tokenizer, T5ForConditionalGeneration, Trainer, TrainingArguments

# Load the dataset you created
df = pd.read_csv("frontend/components/data/training_dataset.csv")

# Convert to HuggingFace dataset
dataset = Dataset.from_pandas(df)

# Load model and tokenizer
model_name = "t5-small"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

# Preprocess function
def preprocess(example):
    inputs = tokenizer(
        example["input"],
        padding="max_length",
        truncation=True,
        max_length=256
    )

    targets = tokenizer(
        example["target"],
        padding="max_length",
        truncation=True,
        max_length=256
    )

    inputs["labels"] = targets["input_ids"]
    return inputs

# Tokenize dataset
dataset = dataset.map(preprocess)

# Training settings
training_args = TrainingArguments(
    output_dir="models/t5-medical-new",
    per_device_train_batch_size=2,
    num_train_epochs=3,
    logging_steps=100,
    save_steps=500
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset
)

# Train model
trainer.train()

# Save model
model.save_pretrained("models/t5-medical-new")
tokenizer.save_pretrained("models/t5-medical-new")

print("training finished")