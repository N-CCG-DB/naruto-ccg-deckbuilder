import csv
import json
import urllib.request
import io

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTuF9g1q2NZ6YQJqrecEEGXQMWHEydjOQ2HHo0CAKa0Jwtu2pVBOkdWn93zBsU3r-ttB70sBDDLVI3W/pub?output=csv"
OUTPUT_JSON = "cards.json"

def sync_sheets():
    print("Fetching live card database from Google Sheets...")
    
    try:
        req = urllib.request.Request(SHEET_CSV_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            raw_csv = response.read().decode('utf-8')
            
        # io.StringIO allows DictReader to properly parse multiline quoted fields
        csv_file = io.StringIO(raw_csv)
        reader = csv.DictReader(csv_file)
        cards = []

        for row in reader:
            clean_row = {}
            for k, v in row.items():
                if k:
                    key = k.strip().lower()
                    val = v.strip() if v else ""

                    # Convert internal line breaks to <br>
                    if key in ["effect", "flavor"] and val:
                        lines = val.splitlines()
                        val = "<br>".join([line.strip() for line in lines if line.strip()])
                    
                    clean_row[key] = val
            
            if clean_row.get("cardnumber") and clean_row.get("setfolder"):
                if clean_row.get("imgname"):
                    clean_row["imgname"] = clean_row["imgname"].lower()
                
                if clean_row.get("setfolder") and not clean_row.get("set"):
                    clean_row["set"] = clean_row["setfolder"].replace("_", " ").title()
                
                cards.append(clean_row)

        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(cards, f, indent=2, ensure_ascii=False)

        print(f"Success! Updated '{OUTPUT_JSON}' with {len(cards)} cards from Google Sheets.")

    except Exception as e:
        print(f"Error syncing with Google Sheets: {e}")

if __name__ == "__main__":
    sync_sheets()