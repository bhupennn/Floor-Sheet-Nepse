from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import sys
import chromedriver_autoinstaller as chromedriver

# Auto-install ChromeDriver
chromedriver.install()

# Setup Chrome options for headless mode
options = Options()
options.headless = True
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--headless")  # Ensures headless mode is set
options.add_argument("--disable-gpu")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.115 Safari/537.36")

# Initialize the WebDriver
service = Service()
driver = webdriver.Chrome(service=service, options=options)

# URL to scrape
url = 'https://chukul.com/floorsheet'
driver.get(url)

def scrape_table():
    """Scrapes the data table from the page"""
    print("Scraping current page...")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    table = soup.find('div', {'class': 'q-table_container'})
    if not table:
        print("No table found.")
        return []
    
    rows = table.find_all('tr')
    data = []
    for row in rows:
        cols = row.find_all('td')
        cols_text = [col.text.strip() for col in cols]
        if cols_text:
            data.append(cols_text)
    return data

all_data = []
current_page = 1

while True:
    print(f"Scraping page {current_page}...")
    all_data.extend(scrape_table())
    
    # Check for next page button
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, 'div.q-pagination__middle button[aria-label]')
        if next_btn.get_attribute('aria-label') == str(current_page + 1):
            next_btn.click()
            current_page += 1
            time.sleep(5)  # Wait for page load
        else:
            break
    except:
        break

# Convert data to DataFrame
df = pd.DataFrame(all_data, columns=['Transact No.', 'Symbol', 'Buyer', 'Seller', 'Quantity', 'Rate', 'Amount'])

def parse_numeric(value):
    """Convert numeric values to float safely."""
    try:
        return float(''.join(c for c in value if c.isdigit() or c == '.'))
    except:
        return None

for col in ['Quantity', 'Rate', 'Amount']:
    df[col] = df[col].apply(parse_numeric)

df = df.dropna(subset=['Amount'])

date_str = datetime.today().strftime('%Y-%m-%d')
df.to_csv(f'scraped_data_{date_str}.csv', index=False)

print(f"Data saved as scraped_data_{date_str}.csv")

driver.quit()
