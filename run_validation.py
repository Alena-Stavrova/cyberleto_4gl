import random
from excel_reader import read_promo_excel
import promo_checker as checker
import csv

SAMPLE_SIZE = 3 # Hardcoded, change to None for full run

# 1. Read the Excel
items = read_promo_excel("item_list.xlsx")

# 2. Decide which items to check
if SAMPLE_SIZE:
    items_to_check = random.sample(items, min(SAMPLE_SIZE, len(items)))
else:
    items_to_check = items

# 3. Create driver once
driver = checker.create_optimized_driver()
driver.maximize_window()

# 4. Loop through items
results = []
try:
    for item in items_to_check:
        try:
            result = checker.check_product(driver, item)
            results.append(result)
        except Exception as e:
            results.append({
                'sku': item.get('sku', 'unknown'),
                'passed': False,
                'errors': [f"Unexpected error: {str(e)}"]
            })
finally:
    driver.quit()

# 5. Print summary
passed = sum(1 for r in results if r['passed'])
print(f"Results: {passed}/{len(results)} passed")
print(results)
