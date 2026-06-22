"""
Shared utilities for promo validation scripts.
- Driver creation
- Price extraction
- Screenshots
- Field comparison
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
import os
import time

# Create the optimized driver (loads fast, limits images)
def create_optimized_driver():
    # Use Options class to customize WebDriver
    options = Options()
    # Wait for DOM to be interactive (instead of all resources to downloaded)
    options.page_load_strategy = 'eager'
    
    # Block all images, background networking and extensions
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-extensions')
    
    driver = webdriver.Chrome(options=options)
    
    # Longer timeout for initial load
    driver.set_page_load_timeout(60)
    
    return driver

def take_screenshot(name, driver):
    # Create screenshot folder, name screenshot images
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    filename = f"screenshots/{name}_{int(time.time())}.png"
    driver.save_screenshot(filename)
    print(f"(Screenshot saved as: {filename})")
    return filename

def extract_price(price_text):
    # Remove all characters except digits and the comma/dot
    # Only EU, US have dot (23.95 EU - no need to replace), the rest have comma
    clean_text = re.sub(r'[^\d]', '', price_text)  
    try:
        return float(clean_text)
    except ValueError:
        return None

def _compare_field(expected, actual, field_name, errors, case_insensitive=False):
    if case_insensitive:
        match = (str(expected).lower() == str(actual).lower())
    else:
        match = (expected == actual)
    if not match:
        errors.append(f"{field_name} mismatch: expected {expected}, got {actual}")     

