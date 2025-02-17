from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
import time
import pandas as pd
from bs4 import BeautifulSoup
import chromedriver_autoinstaller

# Ensure WebDriver is installed
chromedriver_autoinstaller.install()

# Initialize the Edge WebDriver
options = webdriver.EdgeOptions()
options.add_argument('--headless')  # Enable headless mode
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Initialize the WebDriver without specifying the driver path
driver = webdriver.Edge(options=options)

# URL of the webpage to scrape
url = 'https://chukul.com/floorsheet'
driver.get(url)

try:
    # Initialize an empty list to hold all the data
    all_data = []

    def scrape_current_page():
        """Scrapes the table data from the current page."""
        print("Scraping current page...")
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
        all_data.extend(page_data)

        # Check for next page button
        pagination_buttons = driver.find_elements(By.CSS_SELECTOR, 'div.q-pagination__middle button')
        next_page_button = None
        for button in pagination_buttons:
            if button.get_attribute('aria-label') == str(current_page + 1):  # Find the button for the next page
                next_page_button = button
                break

        if next_page_button:
            next_page_button.click()
            current_page += 1
            time.sleep(5)  # Wait for the next page to load
        else:
            print("No next page button found. Assuming this is the last page.")
            break

    # Create a DataFrame from all the data collected
    df = pd.DataFrame(all_data)

    # Define the header names
    header = ['Transact No.', 'Symbol', 'Buyer', 'Seller', 'Quantity', 'Rate', 'Amount']

    # Adjust headers if necessary
    if df.shape[1] == len(header):  # If column count matches, set the header
        df.columns = header
    else:
        raise ValueError(f"Column count mismatch. DataFrame has {df.shape[1]} columns, but {len(header)} headers provided.")

    # Clean and convert 'Quantity', 'Rate', and 'Amount' to numeric
    def parse_numeric(value):
        try:
            # Remove all non-numeric characters except '.' for decimals
            clean_value = ''.join(c for c in value if c.isdigit() or c == '.')
            return float(clean_value)
        except ValueError:
            return None

    df['Quantity'] = df['Quantity'].apply(parse_numeric)
    df['Rate'] = df['Rate'].apply(parse_numeric)
    df['Amount'] = df['Amount'].apply(parse_numeric)

    # Check for NaN or invalid rows
    if df['Amount'].isnull().any():
        print("Warning: Some rows in 'Amount' column could not be converted. Inspecting...")
        print(df[df['Amount'].isnull()])

    # Calculate the total amount after ensuring all values are numeric
    total_amount = df['Amount'].dropna().sum()  # Exclude NaN values
    print(f"Total rows in DataFrame: {len(df)}")
    print(f"Total Amount: {total_amount:,.2f}")  # Display with commas and 2 decimal places

    # Save DataFrame to Excel
    df.to_excel('scraped_data_final.xlsx', index=False)
    print("Data saved to 'scraped_data_final.xlsx'.")

finally:
    # Close the browser after the operations
    driver.quit()
