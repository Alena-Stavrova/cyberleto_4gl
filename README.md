# cyberleto_4gl

"Cyberleto" (cyber summer) was our big summer promo that ran on June 24-30 2026 on our Russian websites. It is based on our Black Friday/Cybermonday promo campaign that significantly changes the looks of the websites (except the discounts are a bit lower). 

Before the campaign begins, the managers prepare a long spreadsheet with the items to be discounted, their old and new prices, their discounts and some other information. I was responsible for 4glaza and Ru Levenhuk websites, and they have a long list of items for 4glaza, some of which were marked "+" for Ru Levenhuk as well. (Ru Ermenrich had a separte spreadsheet, but it was covered by another QA.) 

I wanted to create a tool that would automate a part of my tasks (a lot of UI checks were still tested manually) and ensure the items in the list had correct prices and discounts when the promo began. Specifically, I wanted:
+ once the promo is on, do a quick smoke test and run through 10-20 random items just to make sure it works
+ during the promo, do at least one full run through the list (possibly overnight)

A test suite includes:
+ item_list - a spreadsheet of items with old and new prices and discounts; the main list is items for 4glaza, but some of them are marked to be discounted on Levenhuk as well
+ excel_reader - goes through the spreadsheet, collects data on each item (sku, name, prices, discounts, whether it should be discounted on Levenhuk) and adds it to a dictionary
+ promo_checker (separate ones for 4gl and lvh) - finds the item by SKU on the website, checks if it has old price (strikethrough) and new price as well as the discount and compares it to the data from the excel reader
+ run_validation (separate ones for 4gl and lvh) - a runner program that runs promo_checker on a specified sample (either full list or random) and collects results and mismatches in a csv file

Some notes after running it:
1. Most of the mismatches were small name mismatches, such as "Super Plossl" in the file not matching "super plössl" on the website. Eventually, I just ignored name mismatches as not real errors.
2. Another annoying mismatch was a SKU mismatch which were also not a real error. On our websites, colors work like this: if I type "81414" in the search (black item, discounted), the results will give me a card for 85312 (same item, but in purple) that may or may not be discounted. The fix for this will involve either going to the product page and checking the other color or selecting another color on a small card, both of which seemed like a hassle - so I didn't add it and just make sure those are genuine multicolored items (it's usually obvious by the name).
3. In addition to this, I found a few real issues, such as incorrect discounts or no discounts, promo conflicts (item listed for 2 promos) and a few items from the list missing on the website. There were 5 issues for LVH and 8 for 4GL which is actually a pretty small number (4GL list has almost 1000 itmes) - meaning my colleagues did a great job setting up the promo. All those issues were promptly fixed as well.
4. I ran 4GL script after work, running my PC through the night (it was my first time running a script that way).

Before running it on our production websites, the promo was set up and tested on our testing ("stage") website. There are some lines in my code hinting on that as well as small "utils" file



