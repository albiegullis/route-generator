import os
import shutil
import subprocess
import sys

# The exact path from your error trace
site_packages = r"C:\Users\albie\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages"

print("Initiating protocol to wipe corrupted packages...")

# 1. Force delete the problem folders and their metadata
for item in os.listdir(site_packages):
    if item.startswith("kagglehub") or item.startswith("kagglesdk"):
        path = os.path.join(site_packages, item)
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            print(f"Deleted zombie file/folder: {item}")
        except Exception as e:
            print(f"Warning: Could not delete {item}. It might be locked by another program. Error: {e}")

print("\nDownloading and installing fresh packages (bypassing cache)...")

# 2. Reinstall cleanly without using locally cached (broken) files
subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", "kagglehub", "kagglesdk"])

print("\nSystem clean and packages reinstalled successfully!")