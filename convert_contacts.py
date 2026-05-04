import csv
import json
import re

def clean_number(phone):
    """Removes spaces, dashes, and adds +91 if needed."""
    if not phone: return None
    # Remove everything except digits and +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    if not cleaned: return None
    
    # Auto-add +91 to 10-digit numbers
    if len(cleaned) == 10 and cleaned.isdigit():
        return "+91" + cleaned
    return cleaned

def convert():
    csv_file = "contacts.csv"
    json_file = "contacts.json"
    
    contacts = {}
    count = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            # specifically for Google Contacts CSV format
            reader = csv.DictReader(f)
            
            for row in reader:
                # 1. Build Name
                first = row.get('First Name', '').strip()
                middle = row.get('Middle Name', '').strip()
                last = row.get('Last Name', '').strip()
                
                full_name = f"{first} {middle} {last}".replace('  ', ' ').strip()
                
                # Fallback if name is empty
                if not full_name:
                    full_name = row.get('Organization Name', '').strip()
                
                if not full_name: continue # Skip if still no name

                # 2. Get Phone (Check Phone 1, then Phone 2)
                raw_phone = row.get('Phone 1 - Value')
                if not raw_phone:
                    raw_phone = row.get('Phone 2 - Value')
                
                final_phone = clean_number(raw_phone)
                
                # 3. Save
                if final_phone:
                    contacts[full_name.lower()] = final_phone
                    count += 1
                    
        # Write to JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(contacts, f, indent=4)
            
        print(f"✅ Success! Converted {count} contacts to {json_file}")
        
    except FileNotFoundError:
        print("❌ Error: 'contacts.csv' not found. Make sure it is in this folder.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    convert()