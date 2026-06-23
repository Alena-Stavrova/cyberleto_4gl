import random
from excel_reader import read_promo_excel
import promo_checker_lvh as checker
import csv
import time
from utils import create_optimized_driver

SAMPLE_SIZE = 3 # Hardcoded, change to None for full run

# 1. Read the Excel
items = read_promo_excel("item_list.xlsx", website="LVH")

# 2. Decide which items to check
if SAMPLE_SIZE:
    items_to_check = random.sample(items, min(SAMPLE_SIZE, len(items)))
else:
    items_to_check = items

# 3. Create driver once
driver = create_optimized_driver()
driver.maximize_window()

# 4. Loop through items
results = []
sku_mismatch_list = []
try:
    for item in items_to_check:
        try:
            result = checker.check_product(driver, item)
            results.append(result)
            if 'SKU mismatch'in result['errors']:
                sku_mismatch_list.append(result)
        except Exception as e:
            results.append({
                'sku': item.get('sku', 'unknown'),
                'passed': False,
                'errors': [f"Unexpected error: {str(e)}"]
            })
finally:
    driver.quit()

# 5. Convert to CSV
fields = ['sku', 'expected_name', 'actual_name', 'expected_old_price', 'actual_old_price', 
          'expected_discount', 'actual_discount', 'expected_new_price', 'actual_new_price', 'errors']

output_file_path = f'promo_check_results_LVH_{time.time()}.csv'

with open(output_file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
    csv_writer = csv.writer(csvfile, delimiter=';')
    csv_writer.writerow(fields)  # header
    for result in results:
        row = [result.get(field, '') for field in fields]
        # Convert errors list to string
        if isinstance(row[-1], list):  # errors is the last field
            row[-1] = ', '.join(row[-1])
        csv_writer.writerow(row)


# 6. Print summary
passed = sum(1 for r in results if r['passed'])
print(f"Results: {passed}/{len(results)} passed")
print(results)
print(f"SKU mismatch, to be reviewed: {len(sku_mismatch_list)} item(s)")
print(sku_mismatch_list)