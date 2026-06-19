from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import random
import os
import traceback
import sys

from config import STAGE_USER, STAGE_PASS
website_main = f"https://{STAGE_USER}:{STAGE_PASS}@stage.4glaza.ru/"

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
  
def close_cookie_popup(driver): 
    try:
        accept_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 
                "#cookie_notice_toast .btn.btn-outline-dark.btn-sm.ml-32.mr-32.flex-shrink-0"))
        )
        accept_button.click()
        print("Cookie popup closed")
        time.sleep(1)
        return True    
     
    except Exception as e:
        return False # Popup already closed or not present

def close_region_popup(driver):
    try:
        decline_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.ID, "cancelLocation"))
        )
        decline_button.click()
        print("Region popup closed")
        time.sleep(1)
        return True    
     
    except Exception as e:
        return False # Popup already closed or not present

def close_timer(driver):
    try:
        close_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".promo-timer__close button[data-close]"))
        )
        close_button.click()
        print("Timer closed")
        time.sleep(1)
        return True    
     
    except Exception as e:
        return False # Popup already closed or not present

def _compare_field(expected, actual, field_name, errors, case_insensitive=False):
    if case_insensitive:
        match = (str(expected).lower() == str(actual).lower())
    else:
        match = (expected == actual)
    if not match:
        errors.append(f"{field_name} mismatch: expected {expected}, got {actual}")        

def search_for_sku(driver, sku):
    wait = WebDriverWait(driver, 20)
    try:
        print("Navigating to main page...")
        driver.get(website_main)
        time.sleep(3)

        close_cookie_popup(driver)
        close_region_popup(driver)
        close_timer(driver)
        
        print("Opening search box...")
        search_box = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "search__input")))
        search_box.click()
        time.sleep(1)
        
        print("Entering SKU...")
        search_input = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "search__input")))
        search_input.clear()
        search_input.send_keys(str(sku))
       
        print("Submitting search...")
        search_input.send_keys(Keys.ENTER)
        print("Waiting for results to load...")

        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".product-card.product-control.product-control_inited.product-card_inited"))
            )
        except:
            time.sleep(5)

        # Find card SKU line, like "Product ID: 83836"
        card_sku_elem = driver.find_element(By.CSS_SELECTOR, '.product-card__id.swiper-no-swiping')
        card_sku = card_sku_elem.text[-5:]
        print(f"SKU on the product card is: {card_sku}")
        
        # Scroll to the element to take screenshot
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card_sku_elem)
        time.sleep(2)
        take_screenshot("search_results", driver)

        if sku == card_sku:        
            print("Search completed successfully")
            return True
        else:
            print(f"✗ First found item doesn't match the search: looked for {sku}, first item is {card_sku}")
            return False
                
    except Exception as e:
        print(f"✗ Search failed: {str(e)}")
        take_screenshot("search_error", driver)
        return False

def scrape_product_card(driver):
    # Assumes we're already on a product card page
    # Returns dict with old_price, new_price, discount_pct, or None for any missing
    old_price_text = driver.find_element(By.CLASS_NAME, "product-card__del").text.lower()
    old_price = extract_price(old_price_text)
    name = driver.find_element(By.CLASS_NAME, "product-card__name").text.lower()

    new_price_text = driver.find_element(By.CLASS_NAME, "product-card__price").text.lower() 
    new_price = extract_price(new_price_text) 
    discount_badge = driver.find_element(By.CSS_SELECTOR, ".badge.badge-danger.badge-promotion").text.lower() 
    discount = int(extract_price(discount_badge))

    return {
        'name': name,
        'old_price': old_price,
        'new_price': new_price,
        'discount': discount
    }


def check_product(driver, item):
    wait = WebDriverWait(driver, 20)
    # item: dict from excel_reader with sku, name, old_price, discount, new_price
    sku = item['sku']
    expected_name = item['name']
    expected_old_price = int(item['old_price'])
    expected_discount = int(item['discount'])
    expected_new_price = int(item['new_price'])
    
    errors = []
    sku_found = search_for_sku(driver, sku)

    if sku_found:
        item_website = scrape_product_card(driver) # Returns a dict {'name': 'ABC', 'old_price': '10000'}
        
        actual_name = item_website['name']
        actual_old_price = int(item_website['old_price'])
        actual_discount = item_website['discount']
        actual_new_price = int(item_website['new_price'])

        _compare_field(expected_name, actual_name, "Name", errors, case_insensitive=True)
        _compare_field(expected_old_price, actual_old_price, "Old price", errors)
        _compare_field(expected_discount, actual_discount, "Discount", errors)
        _compare_field(expected_new_price, actual_new_price, "New price", errors) 

    else:
        actual_name = None
        actual_old_price = None
        actual_discount = None
        actual_new_price = None
        errors.append('SKU mismatch')
    
    result = {
        'sku':                 sku,
        'expected_name':       expected_name,
        'actual_name':         actual_name,
        'expected_old_price':  expected_old_price,
        'actual_old_price':    actual_old_price,
        'expected_discount':   expected_discount,
        'actual_discount':     actual_discount,
        'expected_new_price':  expected_new_price,
        'actual_new_price':    actual_new_price,
        'passed':              len(errors) == 0,
        'errors':              errors,
    }
    return result
    
        
        


