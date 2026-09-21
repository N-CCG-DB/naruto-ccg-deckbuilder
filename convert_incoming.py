import os
from PIL import Image

# ---- Config ----
SOURCE_DIR = "incoming_cards"
QUALITY = 80
# Extensions that will be converted. .webp is intentionally excluded.
CONVERT_EXT = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif")

def main():
    if not os.path.isdir(SOURCE_DIR):
        print(f"ERROR: '{SOURCE_DIR}' folder not found. Create it and drop images in.")
        return

    converted = 0
    skipped = 0
    failed = 0

    for fname in sorted(os.listdir(SOURCE_DIR)):
        src_path = os.path.join(SOURCE_DIR, fname)

        if not os.path.isfile(src_path):
            continue

        ext = os.path.splitext(fname)[1].lower()

        if ext == ".webp":
            print(f"SKIP  {fname}  (already webp)")
            skipped += 1
            continue

        if ext not in CONVERT_EXT:
            print(f"SKIP  {fname}  (unsupported extension)")
            skipped += 1
            continue

        stem = os.path.splitext(fname)[0]
        out_name = f"{stem}.webp"
        out_path = os.path.join(SOURCE_DIR, out_name)

        # Avoid clobbering a pre-existing .webp with the same stem
        if os.path.exists(out_path):
            print(f"SKIP  {fname}  (target {out_name} already exists)")
            skipped += 1
            continue

        try:
            with Image.open(src_path) as img:
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")

                img.save(out_path, "WEBP", quality=QUALITY, method=6)

            orig_size = os.path.getsize(src_path) // 1024
            new_size = os.path.getsize(out_path) // 1024

            os.remove(src_path)

            print(f"OK    {fname} -> {out_name}   ({orig_size} KB -> {new_size} KB)")
            converted += 1

        except Exception as e:
            print(f"FAIL  {fname}  ({e})")
            # Clean up a half-written output if one exists
            if os.path.exists(out_path):
                try:
                    os.remove(out_path)
                except Exception:
                    pass
            failed += 1

    print()
    print(f"Converted: {converted}")
    print(f"Skipped:   {skipped}")
    print(f"Failed:    {failed}")
    print(f"Folder:    {SOURCE_DIR}/")

if __name__ == "__main__":
    main()