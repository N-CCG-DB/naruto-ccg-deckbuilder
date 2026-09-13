import os

DATABASE_DIR = "naruto_ccg_sets_database"

def lowercase_everything():
    if not os.path.exists(DATABASE_DIR):
        print(f"Error: Could not find directory '{DATABASE_DIR}'")
        return

    print("Converting all files and subfolders to lowercase...")
    count = 0

    # Walk bottom-up so files are renamed before parent folders
    for root, dirs, files in os.walk(DATABASE_DIR, topdown=False):
        for file_name in files:
            lower_name = file_name.lower()
            if file_name != lower_name:
                old_path = os.path.join(root, file_name)
                temp_path = os.path.join(root, f"temp_{lower_name}")
                new_path = os.path.join(root, lower_name)
                
                os.rename(old_path, temp_path)
                os.rename(temp_path, new_path)
                count += 1

        for dir_name in dirs:
            lower_name = dir_name.lower()
            if dir_name != lower_name:
                old_path = os.path.join(root, dir_name)
                temp_path = os.path.join(root, f"temp_{lower_name}")
                new_path = os.path.join(root, lower_name)
                
                os.rename(old_path, temp_path)
                os.rename(temp_path, new_path)
                count += 1

    print(f"Success! Automatically lowercased {count} internal files/folders.")

if __name__ == "__main__":
    lowercase_everything()