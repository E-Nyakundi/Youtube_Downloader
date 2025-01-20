from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pickle
import os

def fetch_cookies(cookie_file='cookies.txt'):
    """Fetch YouTube cookies using Selenium and save to a file."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.get("https://www.youtube.com")

    # Perform login manually or automate (if applicable)
    input("Log in to YouTube, then press Enter to continue...")

    # Save cookies in a format compatible with yt-dlp
    with open(cookie_file, "w") as f:
        for cookie in driver.get_cookies():
            f.write(f"{cookie['domain']}\tTRUE\t{cookie['path']}\t{str(cookie.get('secure', 'FALSE')).upper()}\t"
                    f"{cookie.get('expiry', '0')}\t{cookie['name']}\t{cookie['value']}\n")

    driver.quit()
    print(f"Cookies saved to {cookie_file}")

if __name__ == "__main__":
    cookie_path = os.path.join(os.path.dirname(__file__), "cookies.txt")
    fetch_cookies(cookie_path)
