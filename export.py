import os
import re
from pathlib import Path

def debug_export():
    print("--- 🔍 Desktop Path Diagnostic 🔍 ---")
    
    # 1. Get the Desktop path using the most direct Windows method
    # This checks the USERPROFILE environment variable
    user_profile = os.environ.get('USERPROFILE')
    desktop_path = Path(user_profile) / "Desktop"
    
    # 2. Check if a OneDrive Desktop still exists and might be the 'real' one
    onedrive_desktop = Path(user_profile) / "OneDrive" / "Desktop"
    
    print(f"[1] Standard Desktop: {desktop_path}")
    print(f"[2] OneDrive Desktop: {onedrive_desktop}")
    
    # We will use the standard one, but print if it actually exists
    if not desktop_path.exists():
        print("⚠️  Warning: The standard Desktop folder was not found!")
    
    print(f"\nCurrently running in: {os.getcwd()}")
    print("-" * 40)

    raw_input = input("Paste your path: ").strip()
    
    # Clean input
    clean_path = re.sub(r'[\[\]]', '', raw_input)
    clean_path = re.sub(r'(?i)^type\s+', '', clean_path).strip()
    source_path = Path(clean_path)

    if source_path.exists() and source_path.is_file():
        try:
            output_name = f"{source_path.name}.txt"
            final_destination = desktop_path / output_name
            
            content = source_path.read_text(encoding='utf-8')
            final_destination.write_text(content, encoding='utf-8')
            
            print(f"\n✅ DONE!")
            print(f"👉 I saved the file here: {final_destination}")
            print(f"👉 Please go to that folder in File Explorer to see it.")
            
            # Open the file so you can see it works
            os.startfile(final_destination)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
    else:
        print(f"\n❌ Could not find the source file: {source_path}")

    print("\n" + "="*40)
    input("Check the path above, then press ENTER to exit...")

if __name__ == "__main__":
    debug_export()