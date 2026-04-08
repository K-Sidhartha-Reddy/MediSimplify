import pandas as pd

# load dataset
df = pd.read_csv("frontend/components/data/mtsamples.csv")

# keep only transcription column
df = df[["transcription"]]

# remove empty rows
df = df.dropna()

# create input format for T5
df["input"] = "simplify: " + df["transcription"]

# target is same text for now
df["target"] = df["transcription"]

df = df[["input","target"]]

# save new dataset
df.to_csv("frontend/components/data/training_dataset.csv", index=False)

print("dataset created")
