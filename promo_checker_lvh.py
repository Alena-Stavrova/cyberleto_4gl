from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from utils import take_screenshot, extract_price, _compare_field
from config import STAGE_USER, STAGE_PASS

# website_main = f"https://{STAGE_USER}:{STAGE_PASS}@stage.levenhuk.ru/"
website_main = "https://levenhuk.ru/"


def close_cookie_popup(driver): 
    try:
        accept_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 
                "#cookie_notice_alert a.btn.btn-outline-dark.btn-sm.fs-12"))
        )
        accept_button.click()
        print("Cookie popup closed")
        time.sleep(1)
        return True    
     
    except Exception as e:
        return False # Popup already closed or not present

def search_for_sku(driver, sku):
    wait = WebDriverWait(driver, 20)
    try:
        print("Navigating to main page...")
        driver.get(website_main)
        time.sleep(3)

        close_cookie_popup(driver)
                
        print("Opening search box...")
        search_box = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "header__search")))
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
                EC.presence_of_element_located((By.CSS_SELECTOR, ".b-48.pb-md-24"))
            )
        except:
            time.sleep(5)

        # Find card SKU line, like "Product ID: 83836"
        card_sku_elem = driver.find_element(By.CLASS_NAME, 'catalog-card__article')
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
    old_price_text = driver.find_element(By.CLASS_NAME, "catalog-card__price-old").text.lower()
    old_price = extract_price(old_price_text)
    name = driver.find_element(By.CLASS_NAME, "catalog-card__title").text.lower()

    new_price_text = driver.find_element(By.CLASS_NAME, "catalog-card__price").text.lower() 
    new_price = extract_price(new_price_text) 
    discount_badge = driver.find_element(By.CLASS_NAME, "catalog-card__sale").text.lower() 
    discount = int(extract_price(discount_badge))

    return {
        'name': name,
        'old_price': old_price,
        'new_price': new_price,
        'discount': discount
    }


def check_product(driver, item):
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


        


