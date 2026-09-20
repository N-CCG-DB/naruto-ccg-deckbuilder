import os
import json
import re
from collections import defaultdict, Counter

# ---- Config ----
IMAGES_JSON = "cards_from_images.json"
DATABASE_JSON = "exports/card_database.json"
OUTPUT_JSON = "cards.json"
BACKUP_JSON = "cards.json.backup"

# ---- Set folder normalization ----
def normalize_setfolder(folder):
    """Convert 'set_17.5_...' to 'set_175_...' (strip dots)."""
    if not folder:
        return folder
    return folder.replace(".", "")

# ---- Card number normalization for matching ----
def normalize_cardnum(num):
    """
    Normalize a card number for matching:
    - lowercase
    - strip spaces
    - strip leading zeros in the numeric portion
    """
    if not num:
        return ""
    s = num.strip().lower().replace(" ", "")

    def collapse(m):
        prefix, num_part, rest = m.group(1), m.group(2), m.group(3)
        return f"{prefix}{int(num_part)}{rest}"

    s = re.sub(r"^([a-z]+)0+(\d+)([a-z]*)$", collapse, s)
    return s

# ---- Type guessing from card number prefix ----
def guess_card_type(cardnumber):
    """
    Guess card type from the card number prefix.
    Returns '' if unknown (promos).
    """
    s = (cardnumber or "").lower()
    if not s:
        return ""
    if s.startswith("nus") or s.startswith("n"):
        return "Ninja"
    if s.startswith("jus") or s.startswith("j"):
        return "Jutsu"
    if s.startswith("mus") or s.startswith("m"):
        return "Mission"
    if s.startswith("cus") or s.startswith("c"):
        return "Client"
    # p* (pr, prus, ps) = promo, needs manual
    return ""

# ---- Split "x/y" stats ----
def split_stats(combined):
    """
    "1/1" -> ("1", "1")
    ""    -> ("", "")
    "6"   -> ("6", "")
    """
    if not combined:
        return "", ""
    parts = combined.split("/")
    if len(parts) == 1:
        return parts[0].strip(), ""
    if len(parts) >= 2:
        return parts[0].strip(), parts[1].strip()
    return "", ""

# ---- Load files ----
if not os.path.exists(IMAGES_JSON):
    print(f"ERROR: {IMAGES_JSON} not found. Run list_images.py first.")
    raise SystemExit(1)

if not os.path.exists(DATABASE_JSON):
    print(f"ERROR: {DATABASE_JSON} not found.")
    raise SystemExit(1)

with open(IMAGES_JSON, "r", encoding="utf-8") as f:
    images = json.load(f)

with open(DATABASE_JSON, "r", encoding="utf-8") as f:
    database = json.load(f)

print(f"Loaded {len(images)} image entries")
print(f"Loaded {len(database)} database entries")
print()

# ---- Build lookups from database ----
db_by_num = {}
db_by_img = {}
db_duplicates = defaultdict(list)

for entry in database:
    num = entry.get("card_number", "")
    img = entry.get("image_path", "")
    img_stem = os.path.splitext(os.path.basename(img))[0].lower() if img else ""

    key = normalize_cardnum(num)
    if key:
        if key in db_by_num:
            db_duplicates[key].append(entry)
        else:
            db_by_num[key] = entry

    if img_stem:
        db_by_img[img_stem] = entry

# ---- Match each image entry ----
matched = 0
matched_by_num = 0
matched_by_img = 0
unmatched = []

for img_entry in images:
    img_num = img_entry.get("cardnumber", "")
    img_stem = os.path.splitext(img_entry.get("imgname", ""))[0].lower()

    key = normalize_cardnum(img_num)
    db_entry = db_by_num.get(key)
    used_num = db_entry is not None

    if db_entry is None and img_stem:
        db_entry = db_by_img.get(img_stem)
        if db_entry is not None:
            used_num = False

    if db_entry is None:
        unmatched.append(img_entry)
        continue

    matched += 1
    if used_num:
        matched_by_num += 1
    else:
        matched_by_img += 1

    # ---- Copy data from db into img entry ----
    img_entry["name"] = db_entry.get("card_name", img_entry.get("name", ""))

    # cardtype: prefer db (none currently), else keep filename guess
    db_type = (db_entry.get("cardtype") or "").strip()
    if db_type:
        img_entry["cardtype"] = db_type

    # Costs
    img_entry["entrancecost"] = db_entry.get("turn_cost", "")
    img_entry["handcost"] = db_entry.get("hand_cost", "")
    img_entry["jutsucost"] = db_entry.get("chakra_cost", "")

    # Stats - split combined form
    h_atk, h_sup = split_stats(db_entry.get("healthy_stats", ""))
    i_atk, i_sup = split_stats(db_entry.get("injured_stats", ""))
    img_entry["combath"] = h_atk
    img_entry["supporth"] = h_sup
    img_entry["combati"] = i_atk
    img_entry["supporti"] = i_sup

    # Other fields
    img_entry["symbol"] = db_entry.get("symbol", "")
    # card_database.json only has 'characteristics' — map to 'attribute'
    img_entry["attribute"] = db_entry.get("characteristics", "")

    # card_set / setfolder
    db_set = db_entry.get("card_set", "")
    if db_set:
        normalized = normalize_setfolder(db_set)
        img_entry["setfolder"] = normalized
        # Preserve a prettier set display name if we have one
        existing_set = img_entry.get("set", "")
        if not existing_set or existing_set.lower() == img_entry.get("setfolder", "").lower():
            img_entry["set"] = db_set.replace("_", " ").title()

# ---- Report ----
print(f"Matched:                {matched} / {len(images)}")
print(f"  matched by cardnum:   {matched_by_num}")
print(f"  matched by imgname:   {matched_by_img}")
print(f"Unmatched:              {len(unmatched)}")
print()

if unmatched:
    print(f"Unmatched card numbers (first 60):")
    for entry in unmatched[:60]:
        print(f"  {entry['setfolder']:<45} {entry['cardnumber']}")
    if len(unmatched) > 60:
        print(f"  ... and {len(unmatched) - 60} more")
    print()

if db_duplicates:
    print(f"Duplicate card numbers in database ({len(db_duplicates)}):")
    for key, entries in list(db_duplicates.items())[:20]:
        names = [e.get("card_name", "?") for e in entries]
        print(f"  {key}: {names}")
    print()

# ---- Write output ----
if os.path.exists(OUTPUT_JSON):
    with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
        original = f.read()
    with open(BACKUP_JSON, "w", encoding="utf-8") as f:
        f.write(original)
    print(f"Backed up original to {BACKUP_JSON}")

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(images, f, indent=2, ensure_ascii=False)

print(f"Wrote {len(images)} entries to {OUTPUT_JSON}")

# ---- Type summary ----
types = Counter(e.get("cardtype", "") or "(unknown)" for e in images)
print()
print("Final type breakdown:")
for t, c in sorted(types.items()):
    print(f"  {t:<15} {c:>5}")