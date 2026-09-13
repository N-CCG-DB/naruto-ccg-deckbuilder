import csv
import json
import urllib.request

# Corrected CSV export URL derived from your published link
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTuF9g1q2NZ6YQJqrecEEGXQMWHEydjOQ2HHo0CAKa0Jwtu2pVBOkdWn93zBsU3r-ttB70sBDDLVI3W/pub?output=csv"
OUTPUT_JSON = "cards.json"

def sync_sheets():
    print("Fetching live card database from Google Sheets...")
    
    try:
        # Request CSV data with standard headers
        req = urllib.request.Request(SHEET_CSV_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            csv_data = response.read().decode('utf-8').splitlines()
            
        reader = csv.DictReader(csv_data)
        cards = []

        for row in reader:
            # Clean up whitespace around keys and values
            clean_row = {k.strip(): v.strip() for k, v in row.items() if k}
            
            # Ensure essential fields exist before including
            if clean_row.get("cardnumber") and clean_row.get("setfolder"):
                # Force lowercase image filenames for WebP compatibility
                if clean_row.get("imgname"):
                    clean_row["imgname"] = clean_row["imgname"].lower()
                
                # Auto-generate or enforce clean set name format if missing
                if clean_row.get("setfolder") and not clean_row.get("set"):
                    clean_row["set"] = clean_row["setfolder"].replace("_", " ").title()
                
                cards.append(clean_row)

        # Output to cards.json
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(cards, f, indent=2, ensure_ascii=False)

        print(f"Success! Updated '{OUTPUT_JSON}' with {len(cards)} cards from Google Sheets.")

    except Exception as e:
        print(f"Error syncing with Google Sheets: {e}")

if __name__ == "__main__":
    sync_sheets()