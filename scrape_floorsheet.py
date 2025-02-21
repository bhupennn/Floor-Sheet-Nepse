from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd

# Set up Chrome options
options = Options()
options.add_argument("--headless")  # Optional: Run in headless mode
options.add_argument("--disable-gpu")  # Optional: Disable GPU (useful for headless)
options.add_argument("--user-data-dir=/path/to/unique/directory")  # Set a unique user data directory
options.add_argument("--no-sandbox")  # Optional: Avoid issues in some environments

# Set up Chrome driver service
service = Service(ChromeDriverManager().install())

# Initialize WebDriver
driver = webdriver.Chrome(service=service, options=options)

# Your target URL
url = "https://chukul.com/floorsheet"

# Open the webpage
driver.get(url)

# Sleep to let the page load fully (can be adjusted or replaced by explicit waits)
time.sleep(3)

# Here, implement your scraping logic
# For example, getting the data table
rows = driver.find_elements(By.XPATH, "//table[@class='floorSheetTable']//tr")

# Initialize an empty list to store data
data = []

# Loop through the rows and extract the required data
for row in rows:
    cols = row.find_elements(By.TAG_NAME, "td")
    cols_text = [col.text for col in cols]
    data.append(cols_text)

# Close the browser after scraping
driver.quit()

# Convert data into a DataFrame
df = pd.DataFrame(data, columns=["Column1", "Column2", "Column3", "Column4", "Column5"])  # Adjust column names

# Save data to Excel
df.to_excel("floorsheet_data.xlsx", index=False)

print("Scraping completed and data saved to floorsheet_data.xlsx")
