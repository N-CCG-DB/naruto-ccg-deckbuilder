import os
import json
import re
from collections import defaultdict, Counter

# ---- Config ----
IMAGES_JSON = "cards_from_images.json"
DATABASE_JSON = "exports/card_database.json"
OUTPUT_JSON = "cards.json"
BACKUP_JSON = "cards.json.backup"

# Letters we strip from the end of a card number when searching for the base card.
# 'b' is deliberately NOT in this set — B-variants are legit separate cards.
STRIPPABLE_SUFFIX_LETTERS = set("ear")

# ---- Set folder normalization ----
def normalize_setfolder(folder):
    """Convert 'set_17.5_...' to 'set_175_...' (strip dots)."""
    if not folder:
        return folder
    return folder.replace(".", "")

# ---- Card number normalization for matching ----
def normalize_cardnum(num):
    """Lowercase, strip spaces, strip leading zeros in numeric portion."""
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
    return ""

# ---- Split "x/y" stats ----
def split_stats(combined):
    if not combined:
        return "", ""
    parts = combined.split("/")
    if len(parts) == 1:
        return parts[0].strip(), ""
    if len(parts) >= 2:
        return parts[0].strip(), parts[1].strip()
    return "", ""

# ---- Strip card number suffix from a name ----
def strip_cardnum_from_name(name, cardnumber):
    """
    If the name ends with the card number (with or without a space), remove it.
    Handles variants: for cardnumber 'm429', strips ' M429', 'M429', ' M429E', etc.
    Also tries the base (without strippable suffix letters).
    Returns cleaned name, or original if nothing to strip.
    """
    if not name or not cardnumber:
        return name

    name_clean = name.strip()
    num_clean = cardnumber.strip()

    # Build candidate suffixes to strip: full number, then progressively
    # remove trailing strippable letters.
    candidates = [num_clean]
    current = num_clean
    while len(current) > 1 and current[-1].lower() in STRIPPABLE_SUFFIX_LETTERS:
        current = current[:-1]
        candidates.append(current)

    # Sort by length, longest first, so we strip the most specific match
    candidates.sort(key=len, reverse=True)

    for suffix in candidates:
        # Match " NAME SUFFIX" or "NAMESUFFIX" at the end (case-insensitive)
        pattern = re.compile(r"\s*" + re.escape(suffix) + r"\s*$", re.IGNORECASE)
        new_name = pattern.sub("", name_clean)
        if new_name != name_clean:
            return new_name.strip()

    return name_clean

# ---- Load ----
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

# ---- Index database ----
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

# ---- Helper: look up base card data (with strippable suffix fallback) ----
def find_db_entry(cardnumber):
    """
    Look up an entry for cardnumber. If not found, progressively strip
    trailing strippable letters ('e', 'a', 'r') and retry.
    Never strips 'b'. Returns (entry, was_stripped) or (None, False).
    """
    key = normalize_cardnum(cardnumber)
    entry = db_by_num.get(key)
    if entry is not None:
        return entry, False

    # Progressively strip strippable letters
    current = cardnumber
    while len(current) > 1 and current[-1].lower() in STRIPPABLE_SUFFIX_LETTERS:
        current = current[:-1]
        key = normalize_cardnum(current)
        entry = db_by_num.get(key)
        if entry is not None:
            return entry, True

    return None, False

# ---- Match ----
matched = 0
matched_direct = 0
matched_base = 0
unmatched = []
base_fallback_used = []  # informational: cards that got data from their base

for img_entry in images:
    img_num = img_entry.get("cardnumber", "")
    img_stem = os.path.splitext(img_entry.get("imgname", ""))[0].lower()

    db_entry, was_stripped = find_db_entry(img_num)

    if db_entry is None and img_stem:
        db_entry = db_by_img.get(img_stem)

    if db_entry is None:
        unmatched.append(img_entry)
        continue

    matched += 1
    if was_stripped:
        matched_base += 1
        base_fallback_used.append(img_num)
    else:
        matched_direct += 1

    # Copy data
    raw_name = db_entry.get("card_name", "") or img_entry.get("name", "")
    img_entry["name"] = strip_cardnum_from_name(raw_name, db_entry.get("card_number", img_num))

    db_type = (db_entry.get("cardtype") or "").strip()
    if db_type:
        img_entry["cardtype"] = db_type

    # Costs — suppress for Jutsu at the data layer for safety
    is_jutsu = (img_entry.get("cardtype", "").strip().lower() == "jutsu")
    if is_jutsu:
        img_entry["entrancecost"] = ""
        img_entry["handcost"] = ""
    else:
        img_entry["entrancecost"] = db_entry.get("turn_cost", "")
        img_entry["handcost"] = db_entry.get("hand_cost", "")
    img_entry["jutsucost"] = db_entry.get("chakra_cost", "")

    # Stats
    h_atk, h_sup = split_stats(db_entry.get("healthy_stats", ""))
    i_atk, i_sup = split_stats(db_entry.get("injured_stats", ""))
    img_entry["combath"] = h_atk
    img_entry["supporth"] = h_sup
    img_entry["combati"] = i_atk
    img_entry["supporti"] = i_sup

    img_entry["symbol"] = db_entry.get("symbol", "")
    img_entry["attribute"] = db_entry.get("characteristics", "")

    # Set folder — keep the one from images (matches disk), normalize dots
    img_entry["setfolder"] = normalize_setfolder(img_entry.get("setfolder", ""))

# ---- Report ----
print(f"Matched:              {matched} / {len(images)}")
print(f"  direct match:       {matched_direct}")
print(f"  via base fallback:  {matched_base}")
print(f"Unmatched:            {len(unmatched)}")
print()

if base_fallback_used:
    print(f"Cards that used base-card data (first 30):")
    for cn in base_fallback_used[:30]:
        print(f"  {cn}")
    if len(base_fallback_used) > 30:
        print(f"  ... and {len(base_fallback_used) - 30} more")
    print()

if unmatched:
    print(f"Unmatched (first 60):")
    for entry in unmatched[:60]:
        print(f"  {entry['setfolder']:<45} {entry['cardnumber']}")
    if len(unmatched) > 60:
        print(f"  ... and {len(unmatched) - 60} more")
    print()

# ---- Backup + write ----
if os.path.exists(OUTPUT_JSON):
    with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
        original = f.read()
    with open(BACKUP_JSON, "w", encoding="utf-8") as f:
        f.write(original)
    print(f"Backed up original to {BACKUP_JSON}")

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(images, f, indent=2, ensure_ascii=False)

print(f"Wrote {len(images)} entries to {OUTPUT_JSON}")

types = Counter(e.get("cardtype", "") or "(unknown)" for e in images)
print()
print("Final type breakdown:")
for t, c in sorted(types.items()):
    print(f"  {t:<15} {c:>5}")