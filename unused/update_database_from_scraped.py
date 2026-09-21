import os
import json
from pathlib import Path

# --- CONFIGURATION ---
CARDS_DB_DIR = "cards_database"
EXPORTS_DIR = "exports"
SCRAPED_JSON_FILE = "scraped_naruto_cards.json"
DB_JSON_FILE = os.path.join(EXPORTS_DIR, "card_database.json")

os.makedirs(EXPORTS_DIR, exist_ok=True)

def load_scraped_data():
    if os.path.exists(SCRAPED_JSON_FILE):
        with open(SCRAPED_JSON_FILE, "r", encoding="utf-8") as f:
            raw_list = json.load(f)
            
        # Index entries by normalized Card Number for fast lookup
        lookup = {}
        for entry in raw_list:
            card_num = entry.get("Card Number", "").lower().replace("-", "").replace("_", "").strip()
            if card_num:
                lookup[card_num] = entry
        return lookup
    else:
        print(f"Error: Could not find '{SCRAPED_JSON_FILE}'.")
        return {}

def update_db():
    scraped_lookup = load_scraped_data()
    if not scraped_lookup:
        return

    cards_path = Path(CARDS_DB_DIR)
    webp_files = list(cards_path.glob("**/*.webp"))

    if not webp_files:
        print("No .webp files found inside cards_database/!")
        return

    updated_database = []

    for img_file in webp_files:
        # Relative image path for Web UI (e.g., "promos/ex001.webp" or "set_01/j001.webp")
        rel_img_path = str(img_file.relative_to(cards_path)).replace("\\", "/")
        
        # Parent directory as set folder
        card_set = img_file.parent.name if img_file.parent != cards_path else "standalone"

        # Base card key (e.g. "j001" from "j001.webp" or "j_001.webp")
        base_filename = img_file.stem
        code_key = base_filename.lower().replace("-", "").replace("_", "").strip()

        matched_data = scraped_lookup.get(code_key, {})

        card_dict = {
            "card_name": matched_data.get("Card Name", base_filename.upper()),
            "card_number": matched_data.get("Card Number", base_filename.upper()),
            "symbol": matched_data.get("Symbol", ""),
            "turn_cost": matched_data.get("Turn", ""),
            "hand_cost": matched_data.get("Hand", ""),
            "chakra_cost": matched_data.get("Chakra", ""),
            "healthy_stats": matched_data.get("Healthy", ""),
            "injured_stats": matched_data.get("Injured", ""),
            "characteristics": matched_data.get("Attribute", ""),
            "image_path": rel_img_path,
            "card_set": card_set
        }

        updated_database.append(card_dict)
        
        if matched_data:
            print(f"Matched: {rel_img_path} -> {card_dict['card_name']} ({card_dict['card_number']})")
        else:
            print(f"No match in scraped JSON for: {rel_img_path} (added basic entry)")

    # Save to exports/card_database.json
    with open(DB_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_database, f, indent=4, ensure_ascii=False)

    print("\n===========================================")
    print(f"Done! Saved {len(updated_database)} entries to {DB_JSON_FILE}")
    print("===========================================")

if __name__ == "__main__":
    update_db()