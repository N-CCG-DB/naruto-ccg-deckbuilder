import os
import json

DATABASE_DIR = "Naruto_CCG_Sets_Database"
OUTPUT_FILE = "cards.json"
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')

def guess_card_type(filename):
    """Detect card type based on filename prefix."""
    fn = filename.lower()
    if fn.startswith('n'): return "Ninja"
    if fn.startswith('j'): return "Jutsu"
    if fn.startswith('m'): return "Mission"
    if fn.startswith('c'): return "Client"
    if fn.startswith('pr') or fn.startswith('ex'): return "Promo (Needs Type)"
    return "Ninja"

def scan_database():
    if not os.path.exists(DATABASE_DIR):
        print(f"Error: Folder '{DATABASE_DIR}' not found in current directory.")
        return

    cards = []
    print("Scanning Naruto CCG sets with updated rulebook schema...")

    for set_folder in sorted(os.listdir(DATABASE_DIR)):
        set_path = os.path.join(DATABASE_DIR, set_folder)
        
        if os.path.isdir(set_path):
            for filename in sorted(os.listdir(set_path)):
                if filename.lower().endswith(IMAGE_EXTENSIONS):
                    card_number = os.path.splitext(filename)[0].upper()
                    card_type = guess_card_type(filename)
                    
                    # Exact Rulebook Schema
                    card_entry = {
                        "cardNumber": card_number,         # Used as unique card ID & image match
                        "name": card_number,               # Card title (fill in via spreadsheet)
                        "cardType": card_type,             # Ninja, Jutsu, Mission, Client
                        "symbol": ["Fire"],                # Supports multiple: ["Fire", "Lightning"]
                        "entranceCost": 0,                 # On what turn card can be played
                        "handCost": 0,                     # Cards discarded from hand to play
                        "effect": "",                      # Card text & keywords
                        "rarity": "Common",                # Common, Uncommon, Rare, Super Rare, Starter, Promo
                        
                        # Ninja & Client Specifics
                        "characteristics": "",             # E.g. "Leaf / Jonin / Mental Power:3 / Sharingan Eye"
                        
                        # Ninja Specific Stats
                        "combatHealthy": "0",              # Combat value while healthy
                        "supportHealthy": "0",             # Support value while healthy
                        "combatInjured": "0",              # Combat value while injured
                        "supportInjured": "0",              # Support value while injured
                        "combatAttribute": "",             # Weapons, Ninjutsu, Taijutsu, Mind, etc.
                        
                        # Jutsu Specifics
                        "jutsuCost": "",                   # E.g. "1 Fire, 1 Any"
                        "target": "",                      # Target criteria
                        
                        # System File Paths
                        "setFolder": set_folder,
                        "imgName": filename
                    }
                    cards.append(card_entry)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(cards, f, indent=2)

    print(f"Success! Processed {len(cards)} cards into '{OUTPUT_FILE}'.")

if __name__ == "__main__":
    scan_database()