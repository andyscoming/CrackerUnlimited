import shutil
import subprocess
import tempfile
import customtkinter as ctk
from tkinter import filedialog
from tkinter import messagebox
import json
import os
from crackinstall import crack_game
from crackinstall import extract
from crackinstall import download_file
import requests
import re
import patoolib




# Function to save the file path to a data file
def save_file_path(file_path):
    data = {"file_path": file_path}
    with open("path_data.json", "w") as file:
        json.dump(data, file)


# Function to load the saved file path (if it exists), or return default path
def load_file_path():
    default_path = r"C:\Program Files (x86)\Steam"  # Default path
    if os.path.exists("path_data.json"):
        with open("path_data.json", "r") as file:
            data = json.load(file)
            return data.get("file_path", default_path)
    return default_path


# Function to search for game APPID from Steam API
def get_appid_from_steam(game_name):
    url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&l=english&cc=US"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data.get('total', 0) > 0:
            appid = data['items'][0]['id']
            return appid
        else:
            return None
    else:
        return None


# Function to find the largest numbered .txt file in the directory
def get_next_file_number(file_path):
    highest_number = 0
    txt_files = [f for f in os.listdir(file_path) if f.endswith(".txt")]

    # Use regex to extract numbers from filenames
    for file in txt_files:
        match = re.match(r"(\d+)\.txt", file)
        if match:
            file_number = int(match.group(1))
            if file_number > highest_number:
                highest_number = file_number

    return highest_number + 1


# Function to create a new .txt file with the next number and write the APPID
def create_appid_file(file_path, appid):
    next_number = get_next_file_number(file_path)
    new_file_name = f"{next_number}.txt"
    new_file_path = os.path.join(file_path, new_file_name)

    with open(new_file_path, "w") as file:
        file.write(str(appid))

    print(f"Created {new_file_name} with APPID {appid}")


# Function linked to "Go" button
def go_function():
    file_path = f"{file_path_var.get()}\\AppList"
    game_name = game_name_var.get()

    if file_path and game_name:
        # Save file path
        save_file_path(file_path_var.get())
        print(f"Game Name: {game_name}")
        print(f"File Path: {file_path}")

        # Retrieve the APPID of the game
        appid = get_appid_from_steam(game_name)
        if appid:
            print(f"APPID for '{game_name}' is: {appid}")

            # Create a new file with the APPID
            create_appid_file(file_path, appid)

            # Step 1: Force end the Steam process
            print("Forcing Steam to close...")
            os.system("taskkill /F /IM steam.exe")  # Windows command to kill the Steam process

            # Step 2: Run the DeleteSteamAppCache.exe program
            parent_dir = os.path.dirname(file_path)  # Get the parent directory of the AppList folder
            exe_path = os.path.join(parent_dir, "DeleteSteamAppCache.exe")  # Full path to the exe file

            if os.path.exists(exe_path):
                print(f"Running {exe_path}...")
                subprocess.run([exe_path])  # Run the .exe file
            os.startfile(f"{file_path_var.get()}/DLLinjector.exe")
        else:
            print(f"Game '{game_name}' not found on Steam.")
    else:
        print("Please enter the game name and select a file path.")

# Function to browse and select a file path
def browse_file():
    file_path = filedialog.askdirectory()
    if file_path:
        file_path_var.set(file_path)

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()



def crack_function():
    game_name = game_name_var.get()
    if game_name:
        crack_game(game_name)


def remove_function():
    file_path = f"{file_path_var.get()}\\AppList"
    game_name = game_name_var.get()
    appid = get_appid_from_steam(game_name)

    try:
        txt_files = [f for f in os.listdir(file_path) if f.endswith(".txt")]
        files_removed = 0

        for file in txt_files:
            file_full_path = os.path.join(file_path, file)

            with open(file_full_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            # Ensure file is closed before attempting to delete it
            if int(content) == int(appid):
                os.remove(file_full_path)
                print(f"Removed: {file}")
                files_removed += 1

        if files_removed == 0:
            print("No matching file found.")
        else:
            print(f"Total files removed: {files_removed}")

    except Exception as e:
        print(f"Error: {e}")

def reinstall_function():
    download_file(r"https://github.com/andyscoming/CrackerUnlimited/blob/main/NormalMode.rar","NormalMode.rar", "GreenLuma")
    rar_path = "NormalMode.rar"
    extract_path = file_path_var.get()
    extract(rar_path, extract_path, "crack")

# Create the main application window
ctk.set_appearance_mode("dark")  # Dark mode for a modern look
ctk.set_default_color_theme("blue")  # You can change this to "green", "dark-blue" etc.

root = ctk.CTk()
root.title("Game Setup")
root.geometry("400x540")

# Define tkinter variables
file_path_var = ctk.StringVar(value=load_file_path())  # Pre-fill with saved or default path
game_name_var = ctk.StringVar()

# Create GUI elements with rounded corners
file_label = ctk.CTkLabel(root, text="Select Steam Path:")
file_label.pack(pady=10)

file_path_entry = ctk.CTkEntry(root, textvariable=file_path_var, width=250, height=30, corner_radius=10)
file_path_entry.pack(pady=10)

browse_button = ctk.CTkButton(root, text="Browse", command=browse_file, width=100, height=40, corner_radius=10)
browse_button.pack(pady=10)

game_name_label = ctk.CTkLabel(root, text="Game Name:")
game_name_label.pack(pady=10)

game_name_entry = ctk.CTkEntry(root, textvariable=game_name_var, width=250, height=30, corner_radius=10)
game_name_entry.pack(pady=10)

go_button = ctk.CTkButton(root, text="Patch", command=go_function, width=100, height=40, corner_radius=10)
go_button.pack(pady=(20,10))

go_button = ctk.CTkButton(root, text="Install Crack", command=crack_function, width=100, height=40, corner_radius=10)
go_button.pack(pady=(0,10))

go_button = ctk.CTkButton(root, text="Remove Patch", command=remove_function, width=100, height=40, corner_radius=10)
go_button.pack(pady=(0,10))

go_button = ctk.CTkButton(root, text="Reinstall GL", command=reinstall_function, width=100, height=40, corner_radius=10)
go_button.pack(pady=(0,20))

# Run the GUI event loop
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
