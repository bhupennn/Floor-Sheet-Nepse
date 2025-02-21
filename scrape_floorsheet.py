import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import pandas as pd
from bs4 import BeautifulSoup

# Automatically install the correct version of ChromeDriver
chromedriver_autoinstaller.install()

# Set Chrome options
options = Options()
# options.add_argument("--headless")  # Uncomment this line if you want to run Chrome in headless mode (no UI)
# options.add_argument("--user-data-dir=/path/to/new/chrome/profile")  # Ensure this is not causing any conflicts

# Initialize Chrome WebDriver service
service = Service()

# Initialize the WebDriver
driver = webdriver.Chrome(service=service, options=options)

# URL of the webpage to scrape
url = 'https://chukul.com/floorsheet'
driver.get(url)

try:
    # Function to scrape the data from the current page
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

    # Initialize an empty list to hold all the data
    all_data = []

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
            time.sleep(8)  # Wait for the next page to load
        else:
            print("No next page button found. Assuming this is the last page.")
            break

    # Option to manually scrape a specific page
    while True:
        user_input = input("Do you want to scrape a specific page? Type 'yes' to scrape or 'no' to finish: ").strip().lower()
        if user_input == 'yes':
            input("Navigate to the desired page in the browser, then press Enter to scrape...")
            page_data = scrape_current_page()
            all_data.extend(page_data)
        elif user_input == 'no':
            break
        else:
            print("Invalid input. Please type 'yes' or 'no'.")

    # Create a DataFrame from all the data collected
    df = pd.DataFrame(all_data)

    # Define the header names
    header = ['Transact No.', 'Symbol', 'Buyer', 'Seller', 'Quantity', 'Rate', 'Amount']

    # Adjust headers if necessary
    if df.shape[1] == len(header):  # If column count matches, set the header
        df.columns = header
    else:
        raise ValueError(f"Column count mismatch. DataFrame has {df.shape[1]} columns, but {len(header)} headers provided.")

    # Define a function to parse and convert to numeric
    def parse_numeric(value):
        try:
            # Remove all non-numeric characters except '.' for decimals
            clean_value = ''.join(c for c in value if c.isdigit() or c == '.')
            return float(clean_value) if clean_value else None
        except ValueError:
            return None

    # Apply conversion to all relevant columns
    for col in ['Quantity', 'Rate', 'Amount']:
        if col in df.columns:
            df[col] = df[col].apply(parse_numeric)

    # Check for any remaining NaN or invalid rows
    invalid_rows = df[df[['Quantity', 'Rate', 'Amount']].isnull().any(axis=1)]
    if not invalid_rows.empty:
        print("Warning: Some rows contain invalid data after conversion.")
        print(invalid_rows)

    # Recalculate the total amount
    df = df.dropna(subset=['Amount'])  # Drop rows where 'Amount' is NaN
    total_amount = df['Amount'].sum()  # Sum the 'Amount' column
    print(f"Total rows after cleaning: {len(df)}")
    print(f"Total Amount: {total_amount:,.2f}")  # Display with commas and 2 decimal places

    # Save the cleaned DataFrame to Excel
    df.to_excel('scraped_data_final.xlsx', index=False)
    print("Data saved to 'scraped_data_final.xlsx'.")

finally:
    # Close the browser after the operations
    driver.quit()
