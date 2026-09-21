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
    if not folder:
        return folder
    return folder.replace(".", "")

# ---- Card number normalization for matching ----
def normalize_cardnum(num):
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

# ---- Is this DB entry a stub? ----
def is_stub(entry):
    """
    An entry is a stub if its card_name equals its card_number,
    or if it has no card_name at all. Stubs have no real data.
    """
    if not entry:
        return True
    name = (entry.get("card_name") or "").strip()
    num = (entry.get("card_number") or "").strip()
    if not name:
        return True
    if name.lower() == num.lower():
        return True
    return False

# ---- Strip card number suffix from a name ----
def strip_cardnum_from_name(name, cardnumber):
    if not name or not cardnumber:
        return name

    name_clean = name.strip()
    num_clean = cardnumber.strip()

    candidates = [num_clean]
    current = num_clean
    while len(current) > 1 and current[-1].lower() in STRIPPABLE_SUFFIX_LETTERS:
        current = current[:-1]
        candidates.append(current)

    candidates.sort(key=len, reverse=True)

    for suffix in candidates:
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
        # Prefer non-stub entries when duplicates exist
        existing = db_by_num.get(key)
        if existing is None or is_stub(existing):
            db_by_num[key] = entry
        else:
            db_duplicates[key].append(entry)
    if img_stem:
        existing = db_by_img.get(img_stem)
        if existing is None or is_stub(existing):
            db_by_img[img_stem] = entry

# ---- Helper: look up base card data (with strippable suffix fallback) ----
def find_db_entry(cardnumber):
    """
    Look up an entry for cardnumber. If the found entry is a stub (no data),
    or if no entry exists, progressively strip trailing strippable letters
    ('e', 'a', 'r') and retry. Never strips 'b'.
    Returns (entry, was_stripped) or (None, False).
    """
    key = normalize_cardnum(cardnumber)
    entry = db_by_num.get(key)
    if entry is not None and not is_stub(entry):
        return entry, False

    # Progressively strip strippable letters
    current = cardnumber
    while len(current) > 1 and current[-1].lower() in STRIPPABLE_SUFFIX_LETTERS:
        current = current[:-1]
        key = normalize_cardnum(current)
        entry = db_by_num.get(key)
        if entry is not None and not is_stub(entry):
            return entry, True

    # Nothing better found — return the stub if that's all we had
    return None, False

# ---- Match ----
matched = 0
matched_direct = 0
matched_base = 0
unmatched = []
base_fallback_used = []

for img_entry in images:
    img_num = img_entry.get("cardnumber", "")
    img_stem = os.path.splitext(img_entry.get("imgname", ""))[0].lower()

    db_entry, was_stripped = find_db_entry(img_num)

    if db_entry is None and img_stem:
        db_entry = db_by_img.get(img_stem)
        if db_entry is not None and is_stub(db_entry):
            db_entry = None  # stub from img lookup doesn't count

    if db_entry is None:
        unmatched.append(img_entry)
        continue

    matched += 1
    if was_stripped:
        matched_base += 1
        base_fallback_used.append(img_num)
    else:
        matched_direct += 1

    raw_name = db_entry.get("card_name", "") or img_entry.get("name", "")
    img_entry["name"] = strip_cardnum_from_name(raw_name, db_entry.get("card_number", img_num))

    db_type = (db_entry.get("cardtype") or "").strip()
    if db_type:
        img_entry["cardtype"] = db_type

    is_jutsu = (img_entry.get("cardtype", "").strip().lower() == "jutsu")
    if is_jutsu:
        img_entry["entrancecost"] = ""
        img_entry["handcost"] = ""
    else:
        img_entry["entrancecost"] = db_entry.get("turn_cost", "")
        img_entry["handcost"] = db_entry.get("hand_cost", "")
    img_entry["jutsucost"] = db_entry.get("chakra_cost", "")

    h_atk, h_sup = split_stats(db_entry.get("healthy_stats", ""))
    i_atk, i_sup = split_stats(db_entry.get("injured_stats", ""))
    img_entry["combath"] = h_atk
    img_entry["supporth"] = h_sup
    img_entry["combati"] = i_atk
    img_entry["supporti"] = i_sup

    img_entry["symbol"] = db_entry.get("symbol", "")
    img_entry["attribute"] = db_entry.get("characteristics", "")

    img_entry["setfolder"] = normalize_setfolder(img_entry.get("setfolder", ""))

# ---- Report ----
print(f"Matched:              {matched} / {len(images)}")
print(f"  direct match:       {matched_direct}")
print(f"  via base fallback:  {matched_base}")
print(f"Unmatched:            {len(unmatched)}")
print()

if base_fallback_used:
    print(f"Cards that used base-card data (first 40):")
    for cn in base_fallback_used[:40]:
        print(f"  {cn}")
    if len(base_fallback_used) > 40:
        print(f"  ... and {len(base_fallback_used) - 40} more")
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