from datasets import load_dataset
import pandas as pd

dataset = load_dataset("medical_dialog")

df = pd.DataFrame(dataset["train"])

df.to_csv("medical_dataset.csv", index=False)

print("Dataset downloaded!")