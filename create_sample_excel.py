import pandas as pd
from pathlib import Path
import os

print("🔧 Creating proper Excel file for Book Generation System...")

# Create the exact data structure your system expects
data = [
    {
        "title": "The Future of AI in Finance",
        "notes_on_outline_before": "Focus on risk management and regulatory challenges. Include case studies from major banks and fintech companies.",
        "status_outline_notes": "yes"
    },
    {
        "title": "Blockchain Revolution in Banking",
        "notes_on_outline_before": "Explore how blockchain is transforming traditional banking. Cover DeFi, smart contracts, CBDCs, and regulatory frameworks.",
        "status_outline_notes": "no_notes_needed"
    },
    {
        "title": "Machine Learning Applications in Healthcare",
        "notes_on_outline_before": "Discuss AI in diagnostics, treatment planning, drug discovery, and patient monitoring. Include ethical considerations.",
        "status_outline_notes": "yes"
    }
]

# Create DataFrame with EXACT column names
df = pd.DataFrame(data)

# Ensure the inputs directory exists
os.makedirs("inputs", exist_ok=True)

# Save to Excel
excel_path = "inputs/books.xlsx"
df.to_excel(excel_path, index=False, sheet_name="Sheet1")

print(f"✅ Created Excel file: {excel_path}")
print(f"✅ File size: {os.path.getsize(excel_path)} bytes")
print(f"\n📋 Columns created: {list(df.columns)}")
print(f"\n📊 Data preview:")
print(df)
print(f"\nTo import, run: python main.py import-from-excel --excel-path {excel_path}")