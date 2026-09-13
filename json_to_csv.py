import json
import csv
import os

JSON_FILE = "cards.json"
CSV_FILE = "naruto_cards_export.csv"

def format_set_name(set_folder):
    if not set_folder:
        return ""
    # Replace underscores with spaces and apply Title Case (e.g. set_01 -> Set 01)
    return set_folder.replace("_", " ").title()

def convert_json_to_csv():
    if not os.path.exists(JSON_FILE):
        print(f"Error: Could not find {JSON_FILE} in current directory.")
        return

    print(f"Reading {JSON_FILE}...")
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        cards = json.load(f)

    if not cards:
        print("cards.json is empty!")
        return

    # Your exact schema order
    fieldnames = [
        "cardnumber",
        "name",
        "cardtype",
        "setfolder",
        "imgname",
        "set",
        "entrancecost",
        "handcost",
        "symbol",
        "combath",
        "supporth",
        "combati",
        "supporti",
        "attribute",
        "effect",
        "jutsucost",
        "rarity",
        "flavor"
    ]

    cleaned_cards = []
    for card in cards:
        folder = card.get("setFolder", card.get("setfolder", ""))
        
        cleaned_card = {
            "cardnumber": card.get("cardNumber", card.get("cardnumber", "")),
            "name": card.get("name", ""),
            "cardtype": card.get("cardType", card.get("cardtype", "")),
            "setfolder": folder,
            "imgname": card.get("imgName", card.get("imgname", "")),
            "set": format_set_name(folder),
            "entrancecost": card.get("entranceCost", card.get("entrancecost", "")),
            "handcost": card.get("handCost", card.get("handcost", "")),
            "symbol": card.get("symbol", card.get("element", "")),
            "combath": card.get("combath", card.get("combat", "")),
            "supporth": card.get("supporth", card.get("support", "")),
            "combati": card.get("combati", ""),
            "supporti": card.get("supporti", ""),
            "attribute": card.get("attribute", card.get("characteristics", "")),
            "effect": card.get("effect", ""),
            "jutsucost": card.get("jutsucost", ""),
            "rarity": card.get("rarity", ""),
            "flavor": card.get("flavor", "")
        }
        cleaned_cards.append(cleaned_card)

    print(f"Writing {len(cleaned_cards)} entries to {CSV_FILE}...")
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_cards)

    print(f"\nSuccess! Open '{CSV_FILE}' and import it into Google Sheets.")

if __name__ == "__main__":
    convert_json_to_csv()