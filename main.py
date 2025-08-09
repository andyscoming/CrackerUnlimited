import json
import pathlib
import shutil
import time
import re
import os
import subprocess
import requests
import tempfile
import zipfile
import rarfile
import wget
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options




# === GLOBAL VARIABLES === #
CHROMEDRIVER_ZIP = 'chromedriver.zip'
CHROMEDRIVER_URL = 'https://chromedriver.storage.googleapis.com/'
PIXELDRAIN_THUMBNAIL_SUFFIX = "/thumbnail"
CHUNK_SIZE = 8192
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
}


# === TEMP SETUP === #
temp = tempfile.gettempdir()
game = input("Game Name?: ")
game_sanitized = re.sub(r'[<>:"/\\|?*]', '', game)
rar_name = game.replace(" ", "_") + ".rar"
game_dir = os.path.join(temp, "gamefiles", game_sanitized)
os.makedirs(game_dir, exist_ok=True)


# === UTILITY FUNCTIONS === #

def process_browser_log_entry(entry):
    response = json.loads(entry['message'])['message']
    return response


def setup_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")

    options.add_argument("--headless=new")

    prefs = {
        "download.prompt_for_download": False,
        "download.default_directory": "/dev/null",  # Or a specific path like "C:\\temp"
        "download_restrictions": 3  # Blocks all downloads
    }

    # Set logging prefs as a capability
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    options.add_experimental_option("prefs", prefs)


    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def wait_and_mute_setup_tmp(timeout=10):
    print("Waiting for setup.tmp to appear...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process and session.Process.name().lower() == "setup.tmp":
                print("Found setup.tmp, muting...")
                session.SimpleAudioVolume.SetMute(1, None)
                return True
        time.sleep(0.2)
    print("setup.tmp not found in time.")
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
                    print(f"\rDownloading {label}: {percent:.2f}% at {1 / 100 * speed / 1024:.2f} MB/s", end="")
        print(f"\nDownload of {label} complete.")
    else:
        print(f"Failed to download {label}. Status code: {response.status_code}")


import subprocess
import os

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


def install_game():
    try:
        setup_path = os.path.join(game_dir, "extract", "setup.exe")

        # Start setup.exe with flags
        proc = subprocess.Popen([
            setup_path,
            "/norestart",
            "/sp-",
            "/suppressmsgboxes",
            "/nocancel"
        ])

        # Try to mute setup.tmp during install
        wait_and_mute_setup_tmp(timeout=15)

        proc.wait()
    except Exception as e:
        raise(e)

def move_game():
    try:
        gamelocation = os.path.join(game_dir, "extract")
        dirs = os.listdir(gamelocation)
        dirs.remove("Read_Me_Instructions.txt")
        dirs.remove("STEAMRIP » Free Pre-installed Steam Games.url")
        dirs.remove("_CommonRedist")
        shutil.move(rf"{gamelocation}\{dirs[0]}", r"C:\Games")
    except Exception as e:
        print(e)


def install_fix():
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

# === DOWNLOAD SOURCES === #


def getOnlineFix():
    link = "null"


    driver.get(f"https://online-fix.me/index.php?do=search&subaction=search&story={game.translate(str.maketrans('', '', r",.:;'\"[]\\|"))}")

    time.sleep(3)

    user = driver.find_element(By.NAME, "login_name")
    password = driver.find_element(By.NAME, "login_password")

    user.send_keys("Anden_5335")
    password.send_keys("01q9g29dc12")
    driver.execute_script("dologin();")

    time.sleep(2)

    gameOptions = driver.find_elements(By.CLASS_NAME, "news-search")

    # Collect the links first, so we don't reuse stale elements after navigation
    game_links = [i.find_element(By.CLASS_NAME, "big-link").get_attribute("href") for i in gameOptions]

    max_attempts = 3  # change this to whatever max you want

    for x, result in enumerate(game_links):
        if x >= max_attempts:
            print("Reached maximum number of attempts.")
            break

        answer = input(f"Is {result} your game? (Y/N): ").strip().upper()
        if answer == "Y":
            try:
                driver.get(result)
                break  # stop after finding the correct game
            except Exception as e:
                print(f"Failed to open {result}: {e}")
        else:
            print("Skipping this one...")

    time.sleep(5)

    try:
        link = driver.find_element(By.XPATH, f"//a[contains(@href,'https://uploads.online-fix.me:2053/uploads/')]")
        url = link.get_attribute("href")
        print("Using upload link")
    except:
        print("No link found for uploads")


    if link == "null":
        try:
            link = driver.find_element(By.XPATH, f"//a[contains(@href,'https://hosters.online-fix.me:2053/')]")
            url = link.get_attribute("href")
            print("Using hoster link")
        except:
            print("No link found for hosters")
            print("No valid download found")

    driver.execute_script("arguments[0].click();", link)

    time.sleep(2)

    driver.get(url)

    time.sleep(2)

    driver.find_element(By.XPATH, "//a[contains(@href,'Fix%20Repair/')]").click()

    time.sleep(1)

    fixrepairurl = driver.find_element(By.XPATH, "/html/body/pre/a[2]").get_attribute("href")

    all_cookies=driver.get_cookies()
    cookies_dict = {}
    for cookie in all_cookies:
        cookies_dict[cookie['name']] = cookie['value']




    # Replace these with your actual cookie values
    cookies = {
        "online_fix_auth": cookies_dict['online_fix_auth'],
        "cf_clearance": cookies_dict['cf_clearance']
    }

    output_rar = rf"{game_dir}\{game_sanitized}_Fix_Repair_Steam_V2_Generic.rar"
    download_file(fixrepairurl, output_rar, "OnlineFix", cookies)

def download_game_steamrip():

    driver.get(f"https://steamrip.com/?s={game.replace(' ', '+')}")
    time.sleep(1)
    result = driver.find_elements(By.CLASS_NAME, "tie-standard")[0]

    if ((input(f"Is this your game (Y/N)?: '{result.find_element(By.XPATH, './div/a').text}' ").capitalize()=="Y")):
        result.click()
    else:
        return
    time.sleep(3)

    host = "null"

    try:
        hostlink = driver.find_element(By.XPATH, "//a[contains(@href,'pixeldrain.com')]").get_attribute('href')
        driver.get(hostlink)
        print("PixelDrain file hoster found")
        host = "PixelDrain"
    except:
        pass

    if host == "null":

        try:
            print("PixelDrain not found, trying BuzzHeavier")
            hostlink = driver.find_element(By.XPATH, "//a[contains(@href,'buzzheavier.com')]").get_attribute('href')
            driver.get(hostlink)
            print("BuzzHeavier file hoster found")
            host = "BuzzHeavier"
        except:
            pass

    time.sleep(4)

    direct_url = extract_direct_link_from_page(host)
    output_path = os.path.join(game_dir, rar_name)
    download_file(direct_url, output_path, "SteamRip")
    extract(output_path, os.path.join(game_dir, "extract"))


def download_game_fitgirl():
    driver.get(f"https://fitgirl-repacks.site/?s={game.replace(' ', '+')}")
    time.sleep(1)


    result = driver.find_elements(By.CLASS_NAME, "category-lossless-repack")[0].find_element(By.XPATH, "header/h1/a")
    if (input(f"Is this your game (Y/N)?: '{result.text}' ").capitalize()=="Y"):
        result.click()
    else:
        raise

    time.sleep(1)

    host = "null"
    try:
        hostlink = driver.find_element(By.XPATH, ".//*[contains(text(), 'Filehoster: FuckingFast')]").get_attribute('href')
        driver.get(hostlink)
        print("FuckingFast file hoster found")
        host = "FuckingFast"
    except:
        try:
            print("FuckingFast not found, trying PixelDrain")
            hostlink = driver.find_element(By.XPATH, ".//*[contains(text(), 'Filehoster: PixelDrain')]").get_attribute('href')
            driver.get(hostlink)
            print("PixelDrain file hoster found")
            host = "PixelDrain"
        except:
            pass

    if host == "null":
        print("No valid hoster found. Skipping FitGirl.")
        return

    time.sleep(1)


    if "paste" in hostlink:

            if host == "FuckingFast":
                downloadlinks = driver.find_element(By.ID, "downloadlinks").find_element(By.XPATH, "..").find_elements(By.XPATH, ".//a[contains(@href,'fitgirl-repacks.site')]")
            if host == "PixelDrain":
                downloadlinks = driver.find_element(By.ID, "downloadlinks").find_element(By.XPATH, "..").find_elements(By.XPATH, ".//a[contains(@href,'pixeldrain')]")


            urls = [link.get_attribute("href") for link in downloadlinks]

            for x, url in enumerate(urls):
                driver.get(url)
                output_path = os.path.join(game_dir, f"{game_sanitized}.part{str(x+1).zfill(3)}.rar")
                download_file(extract_direct_link_from_page(host), output_path, f"part {x+1}/{len(urls)}")

            first_part = os.path.join(game_dir, f"{game_sanitized}.part001.rar")
            extract(first_part, os.path.join(game_dir, "extract"))


    else:
        output_path = os.path.join(game_dir, rar_name)
        download_file(extract_direct_link_from_page(host), output_path, "FitGirl")
        extract(output_path, os.path.join(game_dir, "extract"))


def extract_direct_link_from_page(host):
    if host == "FuckingFast":
        html = driver.page_source
        match = re.search(r'window\.open\(["\'](https://fuckingfast\.co/dl/[^\s"\']+)["\']\)', html)
        return match.group(1) if match else None
    if host == "PixelDrain":
        meta_tag = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:image"]')
        full_url = meta_tag.get_attribute("content")
        direct_url = full_url.replace(PIXELDRAIN_THUMBNAIL_SUFFIX, "")
        return direct_url
    if host == "BuzzHeavier":
        for _ in range(3):
            driver.find_element(By.XPATH, ".//*[contains(text(), 'Download')]").click()
            time.sleep(1)  # give some time for requests to fire

        browser_log = driver.get_log('performance')
        events = [process_browser_log_entry(entry) for entry in browser_log]
        events = [event for event in events if event.get("method") == "Network.responseReceived"]

        for event in events:
            response = event.get("params", {}).get("response", {})
            url = response.get("url", "")
            if "flashbang.sh" in url:
                return url  # ✅ Return direct download URL
        return None  # if not found

def download_game():
    try:
        download_game_fitgirl()
        install_game()
        return
    except:
        print("FitGirl download failed. Trying SteamRip...")

    try:
        download_game_steamrip()
        move_game()
        return
    except:
        print("SteamRip download also failed. Exiting.")
        exit()

# === MAIN === #

driver = setup_driver()


download_game()
time.sleep(1)
try:

    getOnlineFix()
    install_fix()
    for file_path in find_onlinefix_files(os.path.join(r"C:\Games", game_sanitized)):
        modify_fake_appid(file_path, 105600)
except Exception as e:
    print("No online fix found")




shutil.rmtree(game_dir)

print("All Done!")
