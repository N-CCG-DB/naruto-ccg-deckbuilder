import os
from PIL import Image

DATABASE_DIR = "naruto_ccg_sets_database"
TARGET_SIZE = (750, 1050)
QUALITY = 80

def batch_convert():
    if not os.path.exists(DATABASE_DIR):
        print(f"Error: Folder '{DATABASE_DIR}' not found.")
        return

    converted_count = 0
    skipped_count = 0
    print("Starting smart conversion to WEBP (80% quality)...")

    for root, _, files in os.walk(DATABASE_DIR):
        for file in files:
            # Skip files that are ALREADY converted .webp assets
            if file.lower().endswith('.webp'):
                skipped_count += 1
                continue

            # Only process raw/uncompressed additions (.jpg, .jpeg, .png)
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                file_path = os.path.join(root, file)
                
                try:
                    with Image.open(file_path) as img:
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                            
                        img.thumbnail(TARGET_SIZE, Image.Resampling.LANCZOS)
                        
                        base_name = os.path.splitext(file_path)[0]
                        webp_path = f"{base_name}.webp"
                        
                        # Save new optimized WebP
                        img.save(webp_path, "WEBP", quality=QUALITY, optimize=True)
                    
                    # Remove the original uncompressed source file
                    os.remove(file_path)
                    converted_count += 1
                    
                    if converted_count % 50 == 0:
                        print(f"Processed {converted_count} new images...")

                except Exception as e:
                    print(f"Error processing {file}: {e}")

    print(f"\nFinished! Converted {converted_count} new images.")
    print(f"Skipped {skipped_count} existing .webp files.")

if __name__ == "__main__":
    batch_convert()