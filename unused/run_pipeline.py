import os
import json
import re
import hashlib
from pathlib import Path
from PIL import Image

# --- CONFIGURATION ---
INCOMING_DIR = "incoming_cards"
CARDS_DB_DIR = "cards_database"
EXPORTS_DIR = "exports"
MANIFEST_FILE = ".processed_manifest.json"
DB_JSON_FILE = os.path.join(EXPORTS_DIR, "card_database.json")
SCRAPED_JSON_FILE = "scraped_naruto_cards.json"  # Looking in root directory

os.makedirs(INCOMING_DIR, exist_ok=True)
os.makedirs(CARDS_DB_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)

# --- UTILITY FUNCTIONS ---
def load_manifest():
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_manifest(manifest):
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)

def load_database():
    if os.path.exists(DB_JSON_FILE):
        with open(DB_JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_database(data):
    with open(DB_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_scraped_data():
    if os.path.exists(SCRAPED_JSON_FILE):
        with open(SCRAPED_JSON_FILE, "r", encoding="utf-8") as f:
            raw_list = json.load(f)
            
        # Index entries by normalized Card Number for instant lookup
        lookup = {}
        for entry in raw_list:
            card_num = entry.get("Card Number", "").lower().replace("-", "").replace("_", "").strip()
            if card_num:
                lookup[card_num] = entry
        return lookup
    else:
        print(f"Warning: {SCRAPED_JSON_FILE} not found in project root.")
        return {}

def get_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def clean_filename(filename):
    name, _ = os.path.splitext(filename)
    cleaned_name = name.lower().replace(" ", "_")
    cleaned_name = re.sub(r'[^a-z0-9_\-]', '', cleaned_name)
    return f"{cleaned_name}.webp"

def clean_folder_name(folder_path_str):
    if folder_path_str in (".", "", "Standalone"):
        return "standalone"
    
    parts = Path(folder_path_str).parts
    cleaned_parts = []
    for part in parts:
        cleaned = part.lower().replace(" ", "_")
        cleaned = re.sub(r'[^a-z0-9_\-]', '', cleaned)
        cleaned_parts.append(cleaned)
    return os.path.join(*cleaned_parts).replace("\\", "/")

# --- STAGE 1: NON-DESTRUCTIVE IMAGE OPTIMIZATION ---
def process_images(manifest):
    print("\n--- STAGE 1: Processing Images & Formatting Folders ---")
    
    incoming_path = Path(INCOMING_DIR)
    valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
    image_files = [p for p in incoming_path.glob('**/*') if p.is_file() and p.suffix.lower() in valid_extensions]

    if not image_files:
        print("No new image files found in incoming_cards/.")
        return manifest, []

    newly_processed_cards = []

    for file_path in image_files:
        file_hash = get_file_hash(file_path)

        if file_hash in manifest:
            print(f"Skipping {file_path.name}: Already in manifest.")
            continue

        relative_parent = file_path.relative_to(incoming_path).parent
        card_set = clean_folder_name(str(relative_parent))

        target_dir = os.path.join(CARDS_DB_DIR, card_set) if card_set != "standalone" else CARDS_DB_DIR
        os.makedirs(target_dir, exist_ok=True)

        target_filename = clean_filename(file_path.name)
        target_path = os.path.join(target_dir, target_filename)

        rel_db_image_path = os.path.relpath(target_path, CARDS_DB_DIR).replace("\\", "/")

        with Image.open(file_path) as img:
            img = img.convert("RGB")
            img.save(target_path, "WEBP", quality=85, optimize=True)

        manifest[file_hash] = {
            "original_filename": file_path.name,
            "processed_filename": target_filename,
            "relative_image_path": rel_db_image_path,
            "set_folder": card_set,
            "status": "compressed"
        }

        newly_processed_cards.append({
            "image_filename": target_filename,
            "image_path": target_path,
            "rel_image_path": rel_db_image_path,
            "card_set": card_set
        })

        os.remove(file_path)
        print(f"Saved: cards_database/{rel_db_image_path}")

    # Clear empty incoming subfolders
    for dirpath, dirnames, filenames in os.walk(INCOMING_DIR, topdown=False):
        if dirpath != INCOMING_DIR and not os.listdir(dirpath):
            os.rmdir(dirpath)

    return manifest, newly_processed_cards

# --- STAGE 2: SCRAPED DATA MATCHING ---
def run_scraped_hydration(new_cards, existing_db):
    print("\n--- STAGE 2: Hydrating Metadata from Scraped JSON ---")
    if not new_cards:
        return existing_db

    scraped_lookup = load_scraped_data()
    db_map = {item.get("image_path"): item for item in existing_db if "image_path" in item}

    for card_info in new_cards:
        rel_img_path = card_info["rel_image_path"]
        card_set = card_info["card_set"]
        
        # Extract base code from filename e.g. "j001" from "j001.webp" or "j_001.webp"
        base_filename = os.path.splitext(os.path.basename(rel_img_path))[0]
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

        db_map[rel_img_path] = card_dict
        
        if matched_data:
            print(f"  Matched [{base_filename}] -> {card_dict['card_name']} ({card_dict['card_number']})")
        else:
            print(f"  No scraped match for [{base_filename}], initialized with image path only.")

    return list(db_map.values())

# --- MAIN EXECUTION ---
def main():
    print("===========================================")
    print("  NARUTO CCG LOCAL CARD PIPELINE (SCRAPER) ")
    print("===========================================")

    manifest = load_manifest()
    database = load_database()

    manifest, new_cards = process_images(manifest)

    if new_cards:
        database = run_scraped_hydration(new_cards, database)

    save_manifest(manifest)
    save_database(database)

    print("\n===========================================")
    print(f"Pipeline Complete! Total entries in DB: {len(database)}")
    print("===========================================")

if __name__ == "__main__":
    main()