import os
import json
import re
import hashlib
from pathlib import Path
from PIL import Image
from ollama import chat
from pydantic import BaseModel, Field

# --- CONFIGURATION ---
INCOMING_DIR = "incoming_cards"
CARDS_DB_DIR = "cards_database"
EXPORTS_DIR = "exports"
MANIFEST_FILE = ".processed_manifest.json"
DB_JSON_FILE = os.path.join(EXPORTS_DIR, "card_database.json")

os.makedirs(INCOMING_DIR, exist_ok=True)
os.makedirs(CARDS_DB_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)

# --- PYDANTIC SCHEMA FOR OLLAMA ---
class CardData(BaseModel):
    card_name: str = Field(description="Full Card Name")
    card_number: str = Field(description="Card Code e.g. N-001 or J-012")
    card_type: str = Field(description="Ninja, Jutsu, Mission, or Client")
    symbol: str = Field(description="Fire, Water, Lightning, Wind, Earth, Void, or None")
    turn_cost: str = Field(description="Turn cost integer or string")
    hand_cost: str = Field(description="Hand cost integer or string")
    chakra_cost: str = Field(description="Chakra cost string or None")
    healthy_stats: str = Field(description="Combat/Support stats if Ninja, else None")
    injured_stats: str = Field(description="Combat/Support stats if Ninja, else None")
    characteristics: str = Field(description="Comma separated traits e.g. Leaf, Male, Genin")
    effect_text: str = Field(description="Complete rule and effect text on the card")
    flavor_text: str = Field(description="Italicized flavor text if present, else empty string")

# --- MANIFEST & DB UTILS ---
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

# --- STAGE 1: NON-DESTRUCTIVE IMAGE OPTIMIZATION & SET TRACKING ---
def process_images(manifest):
    print("\n--- STAGE 1: Processing & Optimizing Images (With Set Tracking) ---")
    
    incoming_path = Path(INCOMING_DIR)
    # Find all image files across all subfolders inside incoming_cards/
    valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
    image_files = [p for p in incoming_path.glob('**/*') if p.is_file() and p.suffix.lower() in valid_extensions]

    if not image_files:
        print("No new image files found in incoming_cards/.")
        return manifest, []

    newly_processed_cards = []

    for file_path in image_files:
        file_hash = get_file_hash(file_path)

        if file_hash in manifest:
            print(f"Skipping {file_path.name}: Already processed previously (Quality Protection).")
            continue

        # Determine set name from parent subfolder name
        relative_parent = file_path.relative_to(incoming_path).parent
        card_set = str(relative_parent) if str(relative_parent) != "." else "Unknown / Standalone"

        target_filename = clean_filename(file_path.name)
        target_path = os.path.join(CARDS_DB_DIR, target_filename)

        with Image.open(file_path) as img:
            img = img.convert("RGB")
            img.save(target_path, "WEBP", quality=85, optimize=True)

        manifest[file_hash] = {
            "original_filename": file_path.name,
            "processed_filename": target_filename,
            "set_folder": card_set,
            "status": "compressed"
        }

        newly_processed_cards.append({
            "image_filename": target_filename,
            "image_path": target_path,
            "card_set": card_set
        })

        # Remove source file after successful processing
        os.remove(file_path)
        print(f"Processed: [{card_set}] {file_path.name} -> {target_filename}")

    # Clean up empty incoming subfolders
    for dirpath, dirnames, filenames in os.walk(INCOMING_DIR, topdown=False):
        if dirpath != INCOMING_DIR and not os.listdir(dirpath):
            os.rmdir(dirpath)

    return manifest, newly_processed_cards

# --- STAGE 2: OLLAMA VISION LOCAL EXTRACTION ---
def run_ai_extraction(new_cards, existing_db):
    print("\n--- STAGE 2: Local Ollama Vision Text & Data Extraction ---")
    if not new_cards:
        print("No new cards require Vision AI extraction.")
        return existing_db

    db_map = {item.get("image_filename"): item for item in existing_db if "image_filename" in item}

    for card_info in new_cards:
        img_path = card_info["image_path"]
        img_filename = card_info["image_filename"]
        card_set = card_info["card_set"]

        print(f"Extracting text from {img_filename} [{card_set}] using llama3.2-vision...")
        
        try:
            response = chat(
                model="llama3.2-vision",
                messages=[{
                    "role": "user",
                    "content": "Examine this Naruto CCG card and extract all details according to the schema accurately.",
                    "images": [img_path]
                }],
                format=CardData.model_json_schema(),
                options={"temperature": 0}
            )

            extracted_obj = CardData.model_validate_json(response.message.content)
            card_dict = extracted_obj.model_dump()
            card_dict["image_filename"] = img_filename
            card_dict["card_set"] = card_set  # Attach tracked set folder name
            
            db_map[img_filename] = card_dict
            print(f"  Successfully catalogued: {card_dict['card_name']} ({card_dict['card_number']}) | Set: {card_set}")

        except Exception as e:
            print(f"  Error extracting data from {img_filename}: {e}")

    return list(db_map.values())

# --- MAIN EXECUTION ---
def main():
    print("===========================================")
    print("  NARUTO CCG ONE-CLICK LOCAL CARD PIPELINE ")
    print("===========================================")

    manifest = load_manifest()
    database = load_database()

    manifest, new_cards = process_images(manifest)

    if new_cards:
        database = run_ai_extraction(new_cards, database)

    save_manifest(manifest)
    save_database(database)

    print("\n===========================================")
    print(f"Pipeline Complete! Master DB contains {len(database)} cards.")
    print("===========================================")

if __name__ == "__main__":
    main()