from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.utils.data import DataLoader
from tqdm import tqdm
import torch
import torch.nn.functional as F
from torch.optim import AdamW

# Use device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load dataset
dataset = load_dataset("json", data_files="./dataset-v1/data.jsonl", split="train")
train_test = dataset.train_test_split(test_size=0.2, seed=42)
train_dataset = train_test["train"]
test_dataset = train_test["test"]

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-small-en")
model = AutoModelForSequenceClassification.from_pretrained("BAAI/bge-small-en", num_labels=2)
model.to(device)

# Tokenization function with truncation and padding length fixed
def tokenize_function(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=512)

# Map tokenizer over datasets
train_dataset = train_dataset.map(tokenize_function, batched=True)
test_dataset = test_dataset.map(tokenize_function, batched=True)

# Set format to torch tensors with necessary columns
train_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
test_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])

# DataLoaders
train_dataloader = DataLoader(train_dataset, batch_size=16, shuffle=True)
test_dataloader = DataLoader(test_dataset, batch_size=16)

# Quick sanity check batch shapes
ts = next(iter(train_dataloader))
print(f"Batch size: {len(ts['input_ids'])}")
print(f"Input IDs shape: {ts['input_ids'].shape}")
print(f"Attention mask shape: {ts['attention_mask'].shape}")
print(f"Labels shape: {ts['label'].shape}")

# Optimizer
optimizer = AdamW(model.parameters(), lr=2e-5)

# Training loop
num_epochs = 3
model.train()
for epoch in range(num_epochs):
    total_loss = 0
    correct = 0
    total = 0

    for batch in tqdm(train_dataloader, desc=f"Epoch {epoch + 1}"):
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["label"].to(device)

        optimizer.zero_grad()
        outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
        loss = outputs.loss
        logits = outputs.logits

        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        preds = torch.argmax(logits, dim=1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)

    avg_loss = total_loss / len(train_dataloader)
    acc = correct / total
    print(f"Epoch {epoch+1} — Loss: {avg_loss:.4f}, Accuracy: {acc:.4f}")

# Evaluation
model.eval()
correct = 0
total = 0

with torch.no_grad():
    for batch in test_dataloader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["label"].to(device)

        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        preds = torch.argmax(outputs.logits, dim=1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)

print(f"Test Accuracy: {correct / total:.4f}")
