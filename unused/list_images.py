import os
import json
import re

# ---- Config ----
DATABASE_DIR = "cards_database"
OUTPUT_FILE = "cards_from_images.json"
IMAGE_EXTENSIONS = (".webp", ".png", ".jpg", ".jpeg")

# Set name lookup: folder name -> pretty display name
# If a folder isn't listed here, we fall back to title-casing the folder name.
SET_DISPLAY_NAMES = {
    "promos": "Promos",
    "set_1_path_of_the_hokage": "Set 1 Path Of The Hokage",
    "set_2_coils_of_the_snake": "Set 2 Coils Of The Snake",
    "set_3_curse_of_the_sand": "Set 3 Curse Of The Sand",
    "set_4_revenge_and_rebirth": "Set 4 Revenge And Rebirth",
    "set_5_dream_legacy": "Set 5 Dream Legacy",
    "set_6_eternal_rivalry": "Set 6 Eternal Rivalry",
    "set_7_quest_for_power": "Set 7 Quest For Power",
    "set_8_battle_for_destiny": "Set 8 Battle For Destiny",
    "set_9_the_chosen": "Set 9 The Chosen",
    "set_10_lineage_of_the_legends": "Set 10 Lineage Of The Legends",
    "set_11_approaching_wind": "Set 11 Approaching Wind",
    "set_12_a_new_chronicle": "Set 12 A New Chronicle",
    "set_13_fateful_reunion": "Set 13 Fateful Reunion",
    "set_14_emerging_alliance": "Set 14 Emerging Alliance",
    "set_15_fortold_prophecy": "Set 15 Fortold Prophecy",
    "set_16_broken_promise": "Set 16 Broken Promise",
    "set_17_will_of_fire": "Set 17 Will Of Fire",
    "set_18_fangs_of_the_snake": "Set 18 Fangs Of The Snake",
    "set_19_path_of_pain": "Set 19 Path Of Pain",
    "set_20_tales_of_the_galiant_sage": "Set 20 Tales Of The Galiant Sage",
    "set_21_shattered_truth": "Set 21 Shattered Truth",
    "set_22_weapons_of_war": "Set 22 Weapons Of War",
    "set_23_invasion": "Set 23 Invasion",
    "set_24_sages_legacy": "Set 24 Sages Legacy",
    "set_25_kage_summit": "Set 25 Kage Summit",
    "set_26_avengers_wrath": "Set 26 Avengers Wrath",
    "set_27_heros_ascension": "Set 27 Heros Ascension",
    "set_28_ultimate_ninja_storm_3": "Set 28 Ultimate Ninja Storm 3",
}

def guess_card_type(filename_stem):
    """
    Guess card type from the filename prefix.
    Returns '' if we can't tell.
    """
    s = filename_stem.lower()
    # Strip trailing stuff like 'e' (errata), 'a'/'b' (variants) for the prefix check
    if s.startswith("nus") or s.startswith("n"):
        return "Ninja"
    if s.startswith("j") or s.startswith("jus"):
        return "Jutsu"
    if s.startswith("m") or s.startswith("mus"):
        return "Mission"
    if s.startswith("c") or s.startswith("cus"):
        return "Client"
    if s.startswith("p"):  # pr, prus, ps, etc.
        return ""  # promo — needs manual review
    return ""

def main():
    if not os.path.isdir(DATABASE_DIR):
        print(f"ERROR: '{DATABASE_DIR}' folder not found. Run this from the project root.")
        return

    cards = []

    # Walk each set folder
    for set_folder in sorted(os.listdir(DATABASE_DIR)):
        set_path = os.path.join(DATABASE_DIR, set_folder)
        if not os.path.isdir(set_path):
            continue

        display_set = SET_DISPLAY_NAMES.get(
            set_folder,
            set_folder.replace("_", " ").title()
        )

        # Walk files inside the set folder
        for root, _, files in os.walk(set_path):
            for fname in sorted(files):
                if not fname.lower().endswith(IMAGE_EXTENSIONS):
                    continue

                stem, ext = os.path.splitext(fname)
                card_number = stem  # filename without extension, e.g. "ex001"

                # Path relative to cards_database/, e.g. "promos/ex001.webp"
                rel_to_db = os.path.relpath(
                    os.path.join(root, fname), DATABASE_DIR
                ).replace("\\", "/")

                cards.append({
                    "cardnumber": card_number,
                    "name": card_number,          # placeholder; fill in later
                    "cardtype": guess_card_type(stem),
                    "setfolder": set_folder,
                    "imgname": fname,
                    "set": display_set,
                    "image_path": rel_to_db,      # handy for later rebuilds
                    "entrancecost": "",
                    "handcost": "",
                    "symbol": "",
                    "combath": "",
                    "supporth": "",
                    "combati": "",
                    "supporti": "",
                    "attribute": "",
                    "effect": "",
                    "jutsucost": "",
                    "rarity": "",
                    "flavor": "",
                    "characteristics": ""
                })

    # Sort: by set folder, then by card number
    cards.sort(key=lambda c: (c["setfolder"], c["cardnumber"].lower()))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cards, f, indent=2, ensure_ascii=False)

    # Report
    print(f"Total images found: {len(cards)}")
    print(f"Written to:         {OUTPUT_FILE}")
    print()

    # Per-set breakdown
    from collections import Counter
    by_set = Counter(c["setfolder"] for c in cards)
    print("Per-set breakdown:")
    for folder, count in sorted(by_set.items()):
        print(f"  {folder:<45} {count:>5}")

    # Type breakdown
    by_type = Counter(c["cardtype"] or "(unknown)" for c in cards)
    print()
    print("Guessed type breakdown:")
    for ctype, count in sorted(by_type.items()):
        print(f"  {ctype:<15} {count:>5}")

if __name__ == "__main__":
    main()