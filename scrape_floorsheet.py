import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from bs4 import BeautifulSoup

# Automatically install and use the correct Chrome WebDriver
chromedriver_autoinstaller.install()

# Initialize Chrome WebDriver
service = Service()
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")  # Maximize window for better scraping
driver = webdriver.Chrome(service=service, options=options)

# URL of the webpage to scrape
url = 'https://chukul.com/floorsheet'
driver.get(url)

try:
    all_data = []  # Store all scraped data

    def scrape_current_page():
        """Scrapes the table data from the current page."""
        print("Scraping current page...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.q-table_container'))
        )
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Locate the table element
        table = soup.find('div', {
            'class': 'q-table_container q-table--cell-separator column no-wrap q-table_card q-table--flat q-table--bordered q-table--no-wrap table-sticky-header-column'
        })

        if not table:
            print("No table found on the current page.")
            return []

        # Extract table rows
        rows = table.find_all('tr')
        page_data = []
        for row in rows:
            cols = row.find_all('td')
            cols_data = [col.text.strip() for col in cols]  # Extract text from each column
            if cols_data:
                page_data.append(cols_data)

        return page_data

    # Scrape all pages
    current_page = 1
    while True:
        print(f"Scraping page {current_page}...")
        page_data = scrape_current_page()
        if not page_data:
            print("No data found on this page. Exiting...")
            break
        all_data.extend(page_data)

        # Check for "Next" page button
        try:
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Next Page"]'))
            )
            next_button.click()
            current_page += 1
            WebDriverWait(driver, 10).until(
                EC.staleness_of(next_button)  # Wait until the next page loads
            )
        except:
            print("No more pages available. Scraping complete.")
            break  # Exit the loop if no next page is found

    # If no data was scraped, exit
    if not all_data:
        print("No data scraped. Exiting script.")
        driver.quit()
        exit()

    # Create a DataFrame from the collected data
    df = pd.DataFrame(all_data)

    # Define the header names
    header = ['Transact No.', 'Symbol', 'Buyer', 'Seller', 'Quantity', 'Rate', 'Amount']

    # Adjust headers if necessary
    if df.shape[1] == len(header):  # If column count matches, set the header
        df.columns = header
    else:
        raise ValueError(f"Column count mismatch. DataFrame has {df.shape[1]} columns, but {len(header)} headers provided.")

    # Function to parse and convert to numeric
    def parse_numeric(value):
        try:
            # Remove all non-numeric characters except '.' for decimals
            clean_value = ''.join(c for c in value if c.isdigit() or c == '.')
            return float(clean_value) if clean_value else None
        except ValueError:
            return None

    # Apply conversion to numeric columns
    for col in ['Quantity', 'Rate', 'Amount']:
        if col in df.columns:
            df[col] = df[col].apply(parse_numeric)

    # Remove NaN values
    df.dropna(subset=['Quantity', 'Rate', 'Amount'], inplace=True)

    # Recalculate the total amount
    total_amount = df['Amount'].sum()
    print(f"Total rows after cleaning: {len(df)}")
    print(f"Total Amount: {total_amount:,.2f}")

    # Save the cleaned DataFrame to Excel
    df.to_excel('scraped_data_final.xlsx', index=False)
    print("Data successfully saved to 'scraped_data_final.xlsx'.")

finally:
    # Close the browser after the operations
    driver.quit()
