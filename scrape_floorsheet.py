from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

# Ensure ChromeDriver is installed
import chromedriver_autoinstaller
chromedriver_autoinstaller.install()

def get_floorsheet_data():
    # Configure Selenium to run in headless mode
    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Launch Chrome WebDriver
    driver = webdriver.Chrome(options=options)
    driver.get("https://chukul.com/floorsheet")

    # Wait for the table to load
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "table"))
    )

    all_data = []

    while True:
        # Get page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        table = soup.find("table")

        if not table:
            print("No table found on the page!")
            break

        rows = table.find_all("tr")
        for row in rows:
            cols = [col.text.strip() for col in row.find_all("td")]
            if cols:
                all_data.append(cols)

        # Try clicking the "Next" button to go to the next page
        try:
            next_button = driver.find_element(By.LINK_TEXT, "Next")
            if "disabled" in next_button.get_attribute("class"):
                break  # No more pages
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(3)  # Wait for the page to load
        except:
            break

    driver.quit()

    # Convert to DataFrame and save as CSV
    df = pd.DataFrame(all_data, columns=["SN", "Trade Time", "Symbol", "Buyer", "Seller", "Quantity", "Rate", "Amount"])

    # Ensure 'data' folder exists
    if not os.path.exists("data"):
        os.makedirs("data")

    # Get today's date for filename
    today_date = datetime.today().strftime('%Y-%m-%d')
    filename = f"data/floorsheet_{today_date}.csv"

    df.to_csv(filename, index=False)
    print(f"✅ Floorsheet data saved as {filename}")

# Run the scraper
if __name__ == "__main__":
    get_floorsheet_data()
