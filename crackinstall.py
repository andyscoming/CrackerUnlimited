import json
import shutil
import time
import re
import os
import subprocess
import requests
import tempfile
import rarfile
from pycaw.pycaw import AudioUtilities
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver

# === GLOBAL CONSTANTS === #
PIXELDRAIN_THUMBNAIL_SUFFIX = "/thumbnail"
CHUNK_SIZE = 8192
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
}

# === UTILITY FUNCTIONS === #
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

def download_file(url, output_path, label, cookies=""):
    response = requests.get(url, stream=True, headers=HEADERS, cookies=cookies)
    total_size = int(response.headers.get("Content-Length", 0))
    downloaded = 0
    start_time = time.time()
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    elapsed = time.time() - start_time
                    speed = downloaded / elapsed if elapsed > 0 else 0
                    percent = (downloaded / total_size) * 100 if total_size else 0
                    print(f"\rDownloading {label}: {percent:.2f}% at {speed/1024/1024:.2f} MB/s", end="")
        print(f"\nDownload of {label} complete.")
    else:
        raise RuntimeError(f"Failed to download {label}. Status code: {response.status_code}")

def extract(rar_path, extract_path, password=None):
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
        subprocess.run(command, check=True, timeout=60)
        print("✅ Extraction successful.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Extraction failed: {e}")
    except subprocess.TimeoutExpired:
        print("❌ Extraction timed out.")

def install_game(game_dir):
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
            time.sleep(1)
        browser_log = driver.get_log('performance')
        events = [process_browser_log_entry(entry) for entry in browser_log]
        events = [event for event in events if event.get("method") == "Network.responseReceived"]
        for event in events:
            url = event.get("params", {}).get("response", {}).get("url", "")
            if "flashbang.sh" in url:
                return url
        return None

# === MAIN FUNCTION === #
def crack_game(game):
    temp = tempfile.gettempdir()
    game_sanitized = re.sub(r'[<>:"/\\|?*]', '', game)
    rar_name = game.replace(" ", "_") + ".rar"
    game_dir = os.path.join(temp, "gamefiles", game_sanitized)
    os.makedirs(game_dir, exist_ok=True)

    driver = setup_driver()

    try:
        # === FitGirl === #
        try:
            driver.get(f"https://fitgirl-repacks.site/?s={game.replace(' ', '+')}")
            time.sleep(1)
            result = driver.find_elements(By.CLASS_NAME, "category-lossless-repack")[0].find_element(By.XPATH, "header/h1/a")
            if input(f"Is this your game (Y/N)?: '{result.text}' ").capitalize() == "Y":
                result.click()
            else:
                raise RuntimeError("User declined FitGirl match.")
            time.sleep(1)
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
                raise RuntimeError("No valid FitGirl hoster.")
            if "paste" in hostlink:
                if host == "FuckingFast":
                    links = driver.find_element(By.ID, "downloadlinks").find_element(By.XPATH, "..").find_elements(By.XPATH, ".//a[contains(@href,'fitgirl-repacks.site')]")
                else:
                    links = driver.find_element(By.ID, "downloadlinks").find_element(By.XPATH, "..").find_elements(By.XPATH, ".//a[contains(@href,'pixeldrain')]")
                urls = [l.get_attribute("href") for l in links]
                for idx, url in enumerate(urls):
                    driver.get(url)
                    output_path = os.path.join(game_dir, f"{game_sanitized}.part{str(idx+1).zfill(3)}.rar")
                    download_file(extract_direct_link_from_page(driver, host), output_path, f"part {idx+1}/{len(urls)}")
                extract(os.path.join(game_dir, f"{game_sanitized}.part001.rar"), os.path.join(game_dir, "extract"))
            else:
                output_path = os.path.join(game_dir, rar_name)
                download_file(extract_direct_link_from_page(driver, host), output_path, "FitGirl")
                extract(output_path, os.path.join(game_dir, "extract"))
            install_game(game_dir)
            print("✅ FitGirl install complete.")
        except Exception as e:
            print(f"FitGirl failed: {e}")

            # === SteamRip === #
            try:
                driver.get(f"https://steamrip.com/?s={game.replace(' ', '+')}")
                time.sleep(1)
                result = driver.find_elements(By.CLASS_NAME, "tie-standard")[0]
                if input(f"Is this your game (Y/N)?: '{result.find_element(By.XPATH, './div/a').text}' ").capitalize() != "Y":
                    raise RuntimeError("User declined SteamRip match.")
                result.click()
                time.sleep(3)
                host = "null"
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
                output_path = os.path.join(game_dir, rar_name)
                download_file(extract_direct_link_from_page(driver, host), output_path, "SteamRip")
                extract(output_path, os.path.join(game_dir, "extract"))
                move_game(game_dir, game_sanitized)
                print("✅ SteamRip install complete.")
            except Exception as e:
                print(f"SteamRip failed: {e}")
                return

        # === OnlineFix === #
        if input(f"Do you want to fix this game for online (Y/N)?: " == "Y"):
            print("Fixing...")
            try:
                driver.get(f"https://online-fix.me/index.php?do=search&subaction=search&story={game.translate(str.maketrans('', '', r',.:;\'\"[]\\|'))}")
                time.sleep(3)
                driver.find_element(By.NAME, "login_name").send_keys("Anden_5335")
                driver.find_element(By.NAME, "login_password").send_keys("01q9g29dc12")
                driver.execute_script("dologin();")
                time.sleep(2)
                gameOptions = driver.find_elements(By.CLASS_NAME, "news-search")
                game_links = [i.find_element(By.CLASS_NAME, "big-link").get_attribute("href") for i in gameOptions]
                for x, result in enumerate(game_links[:3]):
                    if input(f"Is {result} your game? (Y/N): ").strip().upper() == "Y":
                        driver.get(result)
                        break
                time.sleep(5)
                try:
                    link = driver.find_element(By.XPATH, f"//a[contains(@href,'https://uploads.online-fix.me:2053/uploads/')]")
                    url = link.get_attribute("href")
                except:
                    link = driver.find_element(By.XPATH, f"//a[contains(@href,'https://hosters.online-fix.me:2053/')]")
                    url = link.get_attribute("href")
                driver.execute_script("arguments[0].click();", link)
                time.sleep(2)
                driver.get(url)
                time.sleep(2)
                driver.find_element(By.XPATH, "//a[contains(@href,'Fix%20Repair/')]").click()
                time.sleep(1)
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
                print(f"No online fix found: {e}")

    finally:
        driver.quit()
        shutil.rmtree(game_dir)
        print("🎯 All Done!")

# Example use:
# from myscript import crack_game

#crack_game("Terraria")
