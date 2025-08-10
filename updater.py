import os
import sys
import time
import shutil

if len(sys.argv) != 3:
    print("Usage: updater.exe <target_exe> <new_exe>")
    sys.exit(1)

target_exe = sys.argv[1]
new_exe = sys.argv[2]

print("Waiting for main app to close...")
time.sleep(1)  # Give it a moment

# Wait until the file is not locked
for _ in range(30):
    try:
        os.rename(target_exe, target_exe)  # Try to rename to itself
        break
    except PermissionError:
        time.sleep(0.5)
else:
    print("Error: could not access target exe.")
    sys.exit(1)

print("Replacing file...")
shutil.copy2(new_exe, target_exe)

print("Restarting app...")
os.startfile(target_exe)