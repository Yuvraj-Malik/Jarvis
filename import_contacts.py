import csv
import json
import os

CSV_FILE = "my_contacts.csv"
JSON_FILE = "contacts.json"

def import_contacts():
    # 1. Load existing contacts (so we don't delete old ones)
    data = {}
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as f:
            try:
                data = json.load(f)
            except:
                data = {}

    # 2. Read the CSV
    if not os.path.exists(CSV_FILE):
        print(f"❌ Error: Could not find {CSV_FILE}")
        return

    count = 0
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                name = row[0].strip().lower() # Save as lowercase for easy search
                phone = row[1].strip()
                
                # Auto-add +91 if missing (Optional, remove if not needed)
                if len(phone) == 10 and phone.isdigit():
                    phone = "+91" + phone
                
                data[name] = phone
                count += 1
                print(f"   -> Loaded: {row[0]} ({phone})")

    # 3. Save to Brain
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

    print(f"\n✅ Success! Imported {count} contacts into Jarvis.")

if __name__ == "__main__":
    import_contacts()