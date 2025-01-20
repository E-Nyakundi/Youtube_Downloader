from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from datetime import time
def fetch_cookies(cookie_file='cookies.txt'):
    """Fetch YouTube cookies using Selenium and save to a file."""
    options = Options()
    #options.add_argument("--headless")  # Use headless if you want no browser window to show
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.get("https://www.youtube.com")

    # Automate login process
    login_button = driver.find_element(By.XPATH, '//yt-formatted-string[text()="Sign in"]')
    login_button.click()

    # Wait for login form to load
    driver.implicitly_wait(5)  # Wait a bit for the form to appear

    # Input credentials (you can modify this section for your use)
    email_input = driver.find_element(By.ID, 'identifierId')
    email_input.send_keys("your_email_here@gmail.com")
    email_input.send_keys(Keys.RETURN)
    
    driver.implicitly_wait(5)

    password_input = driver.find_element(By.NAME, 'password')
    password_input.send_keys("your_password_here")
    password_input.send_keys(Keys.RETURN)

    # After login, wait for the user to manually complete any additional verification steps
    driver.implicitly_wait(10)

    # Save cookies in a format compatible with yt-dlp
    with open(cookie_file, "w") as f:
        for cookie in driver.get_cookies():
            f.write(f"{cookie['domain']}\tTRUE\t{cookie['path']}\t{str(cookie.get('secure', 'FALSE')).upper()}\t"
                    f"{cookie.get('expiry', '0')}\t{cookie['name']}\t{cookie['value']}\n")

    driver.quit()
    print(f"Cookies saved to {cookie_file}")
