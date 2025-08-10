import shutil
import time
import subprocess
import tempfile
from pycaw.pycaw import AudioUtilities
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
import customtkinter as ctk
from tkinter import filedialog
from tkinter import messagebox
import json
import os
import requests
import re
import ctypes
import sys
import threading

def run_as_admin():
    # Check if script is already running as admin
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False

    if not is_admin:
        # Relaunch with admin rights
        params = " ".join([f'"{arg}"' for arg in sys.argv])
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, params, None, 1
            )
        except Exception as e:
            print(f"Elevation failed: {e}")
        sys.exit()  # Exit original non-admin instance

run_as_admin()

# === GLOBAL CONSTANTS === #
PIXELDRAIN_THUMBNAIL_SUFFIX = "/thumbnail"
CHUNK_SIZE = 1024 * 1024 * 8
HEADERS = {"Connection": "keep-alive", "User-Agent": "Mozilla/5.0"}

LATEST_EXE_URL = "https://github.com/andyscoming/CrackerUnlimited/releases/latest/download/crackerunlimited.exe"
VERSION_URL = "https://raw.githubusercontent.com/andyscoming/CrackerUnlimited/refs/heads/main/version.txt"

UPDATER_URL = "https://github.com/andyscoming/CrackerUnlimited/raw/refs/heads/main/updater.exe"




### UPDATE FUNCTION ###


def get_latest_version():
    try:
        r = requests.get(VERSION_URL, timeout=5)
        r.raise_for_status()
        return r.text.strip()
    except Exception as e:
        print("Version check failed:", e)
        return None

def download_update():
    temp_path = os.path.join(tempfile.gettempdir(), "update.exe")
    print("Downloading update...")
    r = requests.get(LATEST_EXE_URL, stream=True)
    r.raise_for_status()
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(r.raw, f)
    print("Update downloaded:", temp_path)
    return temp_path

def install_update(new_exe_path):
    print("Installing update...")
    updater_exe = ensure_updater()  # Make sure updater exists
    subprocess.Popen([
        updater_exe,
        sys.argv[0],       # Current exe path
        new_exe_path       # Downloaded update path
    ])
    sys.exit()



### HELPER FUNCTIONS ###

def ensure_updater():
    """
    Downloads updater.exe from GitHub if missing or outdated.
    """
    updater_path = os.path.join(os.path.dirname(sys.argv[0]), "updater.exe")

    # Check if updater exists
    if not os.path.exists(updater_path):
        print("Updater not found, downloading...")
        r = requests.get(UPDATER_URL, stream=True)
        r.raise_for_status()
        with open(updater_path, "wb") as f:
            shutil.copyfileobj(r.raw, f)
        print("Updater downloaded:", updater_path)

    return updater_path

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

def stop_steam():
    print("Forcing Steam to close...")
    os.system("taskkill /F /IM steam.exe")  # Windows command to kill the Steam process

def start_steam():
        os.startfile(f"{file_path_var.get()}/DLLinjector.exe")

def restart_steam():
    stop_steam()
    time.sleep(2)
    start_steam()

def process_browser_log_entry(entry):
    response = json.loads(entry['message'])['message']
    return response

def setup_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    options.add_argument("--headless=new")

    prefs = {
        "download.prompt_for_download": False,
        "download.default_directory": "/dev/null",
        "download_restrictions": 3
    }
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    options.add_experimental_option("prefs", prefs)

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def wait_and_mute_setup_tmp(timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process and session.Process.name().lower() == "setup.tmp":
                session.SimpleAudioVolume.SetMute(1, None)
                return True
        time.sleep(0.2)
    return False

def download_file(url, output_path, label, cookies=None):
    global root  # Use the global root instance from your main app

    response = requests.get(url, stream=True, headers=HEADERS, cookies=cookies or {})
    total_size = int(response.headers.get("Content-Length", 0))
    downloaded = 0
    start_time = time.time()
    last_update = 0  # last UI update time

    progress_bar = root.progress_bar
    progress_label = root.progress_label

    progress_bar.pack()
    progress_label.pack()
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    # Only update UI every 0.2s to avoid slowing download
                    now = time.time()
                    if now - last_update >= 1 or downloaded == total_size:
                        elapsed = now - start_time
                        speed = downloaded / elapsed if elapsed > 0 else 0
                        percent = (downloaded / total_size) * 100 if total_size else 0

                        progress_bar.set(percent / 100)  # CTkProgressBar expects 0–1 range
                        progress_label.configure(
                            text=f"{label}: {percent:.2f}% at {speed / 1024 / 1024:.2f} MB/s"
                        )
                        root.update_idletasks()
                        last_update = now

        progress_label.configure(text=f"Download of {label} complete.")
        progress_bar.set(1.0)
        root.update_idletasks()
    else:
        progress_label.configure(
            text=f"Failed to download {label} (status {response.status_code})."
        )
        root.update_idletasks()

def extract(rar_path, extract_path, password=None):
    useroutput("Extracting...")
    os.makedirs(extract_path, exist_ok=True)

    command = [
        r"C:\Program Files\WinRAR\UnRAR.exe",  # Use UnRAR.exe, not WinRAR.exe
        "x",  # eXtract files with full path
        "-y",  # Assume Yes on all prompts
        f"-p{password}",  # 👈 Supply password here; blank ("") if none
        rar_path,
        extract_path
    ]

    print(f"🛠️ Running: {' '.join(command)}")

    try:
        subprocess.run(command, check=True)
        useroutput("✅ Extraction successful.")
    except subprocess.CalledProcessError as e:
        useroutput(f"❌ Extraction failed: {e}")
    except subprocess.TimeoutExpired:
        useroutput("❌ Extraction timed out.")

def install_game(game_dir):
    useroutput("Setting up game, user input required")
    messagebox.showerror("User input required", "Please finish setting up the game manually")
    setup_path = os.path.join(game_dir, "extract", "setup.exe")
    proc = subprocess.Popen([setup_path, "/norestart", "/sp-", "/suppressmsgboxes", "/nocancel"])
    wait_and_mute_setup_tmp(timeout=15)
    proc.wait()

def move_game(game_dir, game_sanitized):
    gamelocation = os.path.join(game_dir, "extract")
    dirs = os.listdir(gamelocation)

    # List of filenames to skip (whitespace-insensitive)
    skip_names = [
        "Read_Me_Instructions.txt",
        "STEAMRIP»FreePre-installedSteamGames.url",
        "_CommonRedist"
    ]
    # Normalize skip_names: remove all spaces
    skip_names = [name.replace(" ", "") for name in skip_names]

    # Filter dirs by removing anything that matches skip_names ignoring spaces
    dirs = [d for d in dirs if d.replace(" ", "") not in skip_names]

    # Move the first remaining directory
    if dirs:
        destination = os.path.join(r"C:\Games", dirs[0])

        # If destination already exists, remove it
        if os.path.exists(destination):
            shutil.rmtree(destination)

        shutil.move(os.path.join(gamelocation, dirs[0]), destination)

def install_fix(game_dir, game_sanitized):
    output_rar = rf"{game_dir}\{game_sanitized}_Fix_Repair_Steam_V2_Generic.rar"
    extract(output_rar, os.path.join(r"C:\Games", game_sanitized), password="online-fix.me")

def modify_fake_appid(file_path, new_fake_appid):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    with open(file_path, 'w', encoding='utf-8') as f:
        for line in lines:
            if line.strip().startswith("FakeAppId="):
                f.write(f"FakeAppId={new_fake_appid}\n")
            else:
                f.write(line)

def find_onlinefix_files(root_dir):
    matches = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if "OnlineFix.ini" in filenames:
            matches.append(os.path.join(dirpath, "OnlineFix.ini"))
    return matches

def extract_direct_link_from_page(driver, host):
    if host == "FuckingFast":
        html = driver.page_source
        match = re.search(r'window\.open\(["\'](https://fuckingfast\.co/dl/[^\s"\']+)["\']\)', html)
        return match.group(1) if match else None
    if host == "PixelDrain":
        meta_tag = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:image"]')
        return meta_tag.get_attribute("content").replace(PIXELDRAIN_THUMBNAIL_SUFFIX, "")
    if host == "BuzzHeavier":
        for _ in range(3):
            driver.find_element(By.XPATH, ".//*[contains(text(), 'Download')]").click()
            time.sleep(5)
        browser_log = driver.get_log('performance')
        events = [process_browser_log_entry(entry) for entry in browser_log]
        events = [event for event in events if event.get("method") == "Network.responseReceived"]
        for event in events:
            url = event.get("params", {}).get("response", {}).get("url", "")
            if "flashbang.sh" in url:
                return url
        return None

def useroutput(text):
    root.progress_label.configure(text=text)
    print(text)

# === MAIN FUNCTIONS === #

def crack_function():
    game = game_name_var.get()
    if game:
        temp = tempfile.gettempdir()
        game_sanitized = re.sub(r'[<>:"/\\|?*]', '', game)
        rar_name = game.replace(" ", "_") + ".rar"
        game_dir = os.path.join(temp, "gamefiles", game_sanitized)
        os.makedirs(game_dir, exist_ok=True)
        useroutput("Setting up driver")
        driver = setup_driver()

        try:
            # === FitGirl === #
            try:
                useroutput("Searching for Fitgirl repack...")
                driver.get(f"https://fitgirl-repacks.site/?s={game.replace(' ', '+')}")
                time.sleep(2)
                result = driver.find_elements(By.CLASS_NAME, "category-lossless-repack")[0].find_element(By.XPATH, "header/h1/a")

                if messagebox.askyesno("User Input", f"Is this your game?: '{result.text}'"):
                    result.click()
                    useroutput("Finding hoster")
                else:
                    raise RuntimeError("User declined FitGirl match")
                time.sleep(5)
                host = "null"
                try:
                    hostlink = driver.find_element(By.XPATH, ".//*[contains(text(), 'Filehoster: FuckingFast')]").get_attribute('href')
                    driver.get(hostlink); host = "FuckingFast"
                except:
                    try:
                        hostlink = driver.find_element(By.XPATH, ".//*[contains(text(), 'Filehoster: PixelDrain')]").get_attribute('href')
                        driver.get(hostlink); host = "PixelDrain"
                    except:
                        pass
                if host == "null":
                    raise RuntimeError("No valid FitGirl hoster. Checking SteamRip")
                else:
                    useroutput(f"Using {host} file hoster")
                time.sleep(5)
                if "paste" in hostlink:
                    useroutput("Multipart download found")
                    if host == "FuckingFast":
                        links = driver.find_element(By.ID, "downloadlinks").find_element(By.XPATH, "..").find_elements(By.XPATH, ".//a[contains(@href,'fitgirl-repacks.site')]")
                    else:
                        links = driver.find_element(By.ID, "downloadlinks").find_element(By.XPATH, "..").find_elements(By.XPATH, ".//a[contains(@href,'pixeldrain')]")
                    time.sleep(5)
                    urls = [l.get_attribute("href") for l in links]
                    for idx, url in enumerate(urls):
                        driver.get(url)
                        output_path = os.path.join(game_dir, f"{game_sanitized}.part{str(idx+1).zfill(3)}.rar")
                        download_file(extract_direct_link_from_page(driver, host), output_path, f"Part {idx+1}/{len(urls)}")
                    extract(os.path.join(game_dir, f"{game_sanitized}.part001.rar"), os.path.join(game_dir, "extract"))
                else:
                    useroutput("One part download found")
                    output_path = os.path.join(game_dir, rar_name)
                    download_file(extract_direct_link_from_page(driver, host), output_path, "FitGirl")
                    extract(output_path, os.path.join(game_dir, "extract"))
                install_game(game_dir)
                useroutput("✅ FitGirl install complete.")
            except Exception as e:
                print(f"FitGirl failed: {e}")

                # === SteamRip === #
                try:
                    useroutput("Searching for SteamRip")
                    driver.get(f"https://steamrip.com/?s={game.replace(' ', '+')}")
                    time.sleep(5)
                    result = driver.find_elements(By.CLASS_NAME, "tie-standard")[0]

                    if not messagebox.askyesno("User Input", f"Is this your game?: '{result.find_element(By.XPATH, './div/a').text}'"):
                        raise RuntimeError("User declined SteamRip match.")
                    result.click()
                    time.sleep(5)
                    host = "null"
                    useroutput("Finding hoster")
                    try:
                        driver.get(driver.find_element(By.XPATH, "//a[contains(@href,'pixeldrain.com')]").get_attribute('href'))
                        host = "PixelDrain"
                    except:
                        try:
                            driver.get(driver.find_element(By.XPATH, "//a[contains(@href,'buzzheavier.com')]").get_attribute('href'))
                            host = "BuzzHeavier"
                        except:
                            pass
                    if host == "null":
                        raise RuntimeError("No valid SteamRip hoster.")
                    else:
                        useroutput(f"Using {host} hoster")
                    output_path = os.path.join(game_dir, rar_name)
                    download_file(extract_direct_link_from_page(driver, host), output_path, "SteamRip")
                    extract(output_path, os.path.join(game_dir, "extract"))
                    move_game(game_dir, game_sanitized)
                    useroutput("✅ SteamRip install complete.")
                except Exception as e:
                    print(f"SteamRip failed: {e}")
                    return

            # === OnlineFix === #

            if messagebox.askyesno("User Input", f"Do you want to fix this game for online?"):
                useroutput("Fixing game...")
                try:
                    driver.get(f"https://online-fix.me/index.php?do=search&subaction=search&story={game.translate(str.maketrans('', '', r',.:;\'\"[]\\|'))}")
                    time.sleep(5)
                    driver.find_element(By.NAME, "login_name").send_keys("Anden_5335")
                    driver.find_element(By.NAME, "login_password").send_keys("01q9g29dc12")
                    driver.execute_script("dologin();")
                    time.sleep(5)
                    gameOptions = driver.find_elements(By.CLASS_NAME, "news-search")
                    game_links = [i.find_element(By.CLASS_NAME, "big-link").get_attribute("href") for i in gameOptions]
                    for x, result in enumerate(game_links[:3]):
                        if messagebox.askyesno("User Input",f"Is {result} your game?"):
                            driver.get(result)
                            break
                    time.sleep(5)
                    try:
                        link = driver.find_element(By.XPATH, f"//a[contains(@href,'https://uploads.online-fix.me:2053/uploads/')]")
                        url = link.get_attribute("href")
                    except:
                        link = driver.find_element(By.XPATH, f"//a[contains(@href,'https://hosters.online-fix.me:2053/')]")
                        url = link.get_attribute("href")
                    useroutput("Fix found")
                    driver.execute_script("arguments[0].click();", link)
                    time.sleep(5)
                    driver.get(url)
                    time.sleep(5)
                    driver.find_element(By.XPATH, "//a[contains(@href,'Fix%20Repair/')]").click()
                    time.sleep(5)
                    fixrepairurl = driver.find_element(By.XPATH, "/html/body/pre/a[2]").get_attribute("href")
                    cookies_dict = {c['name']: c['value'] for c in driver.get_cookies()}
                    cookies = {
                        "online_fix_auth": cookies_dict.get('online_fix_auth', ''),
                        "cf_clearance": cookies_dict.get('cf_clearance', '')
                    }
                    output_rar = rf"{game_dir}\{game_sanitized}_Fix_Repair_Steam_V2_Generic.rar"
                    download_file(fixrepairurl, output_rar, "OnlineFix", cookies)
                    install_fix(game_dir, game_sanitized)
                    for file_path in find_onlinefix_files(os.path.join(r"C:\Games", game_sanitized)):
                        modify_fake_appid(file_path, 105600)
                    print("✅ OnlineFix applied.")
                except Exception as e:
                    print(e)
                    useroutput("No online fix found")


        finally:
            driver.quit()
            shutil.rmtree(game_dir)

            useroutput("🎯 All Done!")
    else:
        messagebox.showerror("Error","Please enter the game name.")

# Function to browse and select a file path
def browse_file():
    file_path = filedialog.askdirectory()
    if file_path:
        file_path_var.set(file_path)

# Function linked to "Go" button
def go_function():
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

            restart_steam()
            messagebox.showinfo("Game patched", f"Game {game_name}:{appid} patched!")


        else:
            messagebox.showerror("No game found", "No game found")

    else:
        print("Please enter the game name and select a file path.")
        messagebox.showerror("Error", "Please enter the game name and select a file path.")

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
            messagebox.showerror("Game not found", "Game not found")
        else:
            print(f"Total files removed: {files_removed}")
            messagebox.showinfo("Game removed", f"Game {game_name}:{appid} removed!")

        restart_steam()

    except Exception as e:
        print(f"Error: {e}")

def reinstall_function():
    stop_steam()
    try:
        download_file(r"https://github.com/andyscoming/CrackerUnlimited/raw/refs/heads/main/NormalMode.rar","NormalMode.rar", "GreenLuma")
        rar_path = "NormalMode.rar"
        extract_path = file_path_var.get()
        extract(rar_path, extract_path, "crack")
        messagebox.showinfo("Success", "GreenLuma successfully reinstalled and updated!")
    except Exception as e:
        print(e)
        messagebox.showerror("Failed to reinstall","Failed to reinstall")

    start_steam()

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()


def start_crack_thread():
    threading.Thread(target=crack_function, daemon=True).start()

def start_reinstall_thread():
    threading.Thread(target=reinstall_function(), daemon=True).start()


if __name__ == "__main__":
    latest = get_latest_version()
    current = "1.0.7"

    if latest and latest != current:
        print(f"New version {latest} found! Updating...")
        new_exe = download_update()
        install_update(new_exe)
    else:
        print("Already up to date!")
    # ---- MAIN APP CODE ----
    print(f"App v{current} running.")
    # Create the main application window
    ctk.set_appearance_mode("dark")  # Dark mode for a modern look
    ctk.set_default_color_theme("dark-blue")  # You can change this to "green", "dark-blue" etc.

    root = ctk.CTk()
    root.title("Game Setup")
    root.geometry("400x560")

    # Define tkinter variables
    file_path_var = ctk.StringVar(value=load_file_path())  # Pre-fill with saved or default path
    game_name_var = ctk.StringVar()

    # Create GUI elements with rounded corners
    file_label = ctk.CTkLabel(root, text="Select Steam Path:")
    file_label.pack(pady=10)

    file_path_entry = ctk.CTkEntry(root, textvariable=file_path_var, width=250, height=30, corner_radius=10)
    file_path_entry.pack(pady=10)

    file_path = f"{file_path_var.get()}\\AppList"


    browse_button = ctk.CTkButton(root, text="Browse", command=browse_file, width=100, height=40, corner_radius=10)
    browse_button.pack(pady=10)

    game_name_label = ctk.CTkLabel(root, text="Game Name:")
    game_name_label.pack(pady=10)

    game_name_entry = ctk.CTkEntry(root, textvariable=game_name_var, width=250, height=30, corner_radius=10)
    game_name_entry.pack(pady=10)

    go_button = ctk.CTkButton(root, text="Patch", command=go_function, width=100, height=40, corner_radius=10)
    go_button.pack(pady=(20,10))

    install_button = ctk.CTkButton(root, text="Install Crack", command=start_crack_thread, width=100, height=40, corner_radius=10)
    install_button.pack(pady=(0,10))

    remove_button = ctk.CTkButton(root, text="Remove Patch", command=remove_function, width=100, height=40, corner_radius=10)
    remove_button.pack(pady=(0,10))

    reinstall_button = ctk.CTkButton(root, text="Reinstall GL", command=start_reinstall_thread, width=100, height=40, corner_radius=10)
    reinstall_button.pack(pady=(0,10))

    root.progress_label = ctk.CTkLabel(root, text="")
    root.progress_label.pack(pady=(0,10))

    root.progress_bar = ctk.CTkProgressBar(root)
    root.progress_bar.pack(pady=(0,20))
    root.progress_bar.set(0)
    root.progress_bar.pack_forget()

    # Run the GUI event loop
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()