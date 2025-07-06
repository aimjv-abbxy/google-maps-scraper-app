# scraper_engine.py (Corrected Version)

import time, re, os, csv, random
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# --- HELPER FUNCTIONS ---

# --- FIXED: Added the missing load_processed_addresses function ---
def load_processed_addresses(filepath):
    """Loads previously scraped Full Business Addresses from a CSV to prevent duplicates."""
    processed_addresses = set()
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', newline='', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                header = next(reader)
                try:
                    address_index = header.index('Full Business Address')
                    for row in reader:
                        if len(row) > address_index and row[address_index] and row[address_index] != 'Not Found':
                            processed_addresses.add(row[address_index])
                except ValueError:
                    # This is not an error, the file might be new
                    pass
    except Exception as e:
        print(f"-> Could not load previous file '{filepath}'. Error: {e}")
    return processed_addresses

def clean_url(url):
    if url and '?' in url: return url.split('?')[0]
    return url

def clean_text(text):
    if not text: return ""
    return re.sub(r'^[||]\s*', '', text).strip()

def extract_business_details(driver):
    details = {}
    try: details["Business Name"] = driver.find_element(By.CSS_SELECTOR, "h1.DUwDvf, h1.fontHeadlineLarge").text
    except NoSuchElementException: details["Business Name"] = "Not Found"
    try:
        review_container = driver.find_element(By.CSS_SELECTOR, "div.F7nice")
        review_text = review_container.text
        rating_match = re.search(r'(\d\.\d|\d)', review_text)
        details["Star Rating"] = rating_match.group(1) if rating_match else "N/A"
        reviews_match = re.search(r'\((\d{1,3}(,\d{3})*|[\d,]+)\)', review_text)
        details["Number of Google Reviews"] = reviews_match.group(1) if reviews_match else "0"
    except NoSuchElementException:
        details["Star Rating"], details["Number of Google Reviews"] = "N/A", "0"
    try:
        pricing_text = driver.find_element(By.CSS_SELECTOR, "span.mgr77e").text
        details["Pricing"] = clean_text(pricing_text.replace('·', ''))
    except NoSuchElementException: details["Pricing"] = "Not Found"
    try:
        address_text = driver.find_element(By.CSS_SELECTOR, "[data-item-id='address']").text
        details["Full Business Address"] = clean_text(address_text)
    except NoSuchElementException: details["Full Business Address"] = "Not Found"
    try:
        raw_url = driver.find_element(By.CSS_SELECTOR, "[data-item-id='authority']").get_attribute("href")
        details["Website URL"] = clean_url(raw_url)
    except NoSuchElementException: details["Website URL"] = "Not Found"
    try:
        phone_text = driver.find_element(By.CSS_SELECTOR, "[data-item-id^='phone:tel:']").text
        details["Phone Number"] = clean_text(phone_text)
    except NoSuchElementException: details["Phone Number"] = "Not Found"
    try:
        hours_container = driver.find_element(By.CSS_SELECTOR, "[jsaction*='pane.openhours']")
        details["Business Hours"] = hours_container.find_element(By.CSS_SELECTOR, "span.ZDu9vd").text
    except NoSuchElementException: details["Business Hours"] = "Not Found"
    try:
        plus_code_text = driver.find_element(By.CSS_SELECTOR, "[data-item-id='oloc']").text
        details["Plus Code"] = clean_text(plus_code_text)
    except NoSuchElementException: details["Plus Code"] = "Not Found"
    return details

def run_scraper(params, update_callback, stop_event):
    keyword, location, country = params['keyword'], params['location'], params['country']
    target_leads, headless, filepath, processed_addresses = params['target_leads'], params['headless'], params['filepath'], params['processed_addresses']
    
    headers = [ "Business Name", "Star Rating", "Number of Google Reviews", "Pricing", "Full Business Address", "Business Hours", "Plus Code", "Phone Number", "Website URL" ]
    delays = {'short': (2, 4), 'medium': (4, 7), 'long': (7, 12)} if target_leads > 50 else {'short': (1, 2.5), 'medium': (2.5, 4), 'long': (4, 7)}
    
    is_new_file = not os.path.exists(filepath) or os.path.getsize(filepath) == 0
    if is_new_file:
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    if headless:
        options.add_argument('--headless')
        options.add_argument("--window-size=1920,1080")
        update_callback("-> Running in headless mode.")

    driver = None
    leads_found_this_run = 0
    
    try:
        with open(filepath, 'a', newline='', encoding='utf-8-sig', buffering=1) as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            service = Service()
            driver = webdriver.Chrome(service=service, options=options)
            
            query = f"{keyword} in {location}, {country}"
            search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
            update_callback(f"Navigating to: {search_url}")
            driver.get(search_url)

            scrollable_feed_selector = 'div[role="feed"]'
            scrollable_element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, scrollable_feed_selector)))
            
            processed_gmaps_link_count = 0
            patience_counter = 0
            max_patience = 3

            while leads_found_this_run < target_leads:
                if stop_event.is_set():
                    update_callback("-> Scraping stopped by user.")
                    break
                    
                all_links_on_page = driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")
                if processed_gmaps_link_count >= len(all_links_on_page):
                    update_callback("-> All visible businesses processed, scrolling to load more...")
                    scrollable_element.send_keys(Keys.END)
                    time.sleep(random.uniform(*delays['medium']))
                    new_link_count = len(driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc"))
                    if new_link_count == processed_gmaps_link_count:
                        patience_counter += 1
                        update_callback(f"  -> Scroll did not reveal new results. Patience: {patience_counter}/{max_patience}")
                        if patience_counter >= max_patience:
                            update_callback("\n-> Reached the end of all search results.")
                            break
                    else: patience_counter = 0
                    continue
                try:
                    link_to_process = all_links_on_page[processed_gmaps_link_count]
                    processed_gmaps_link_count += 1
                    listing_name = link_to_process.get_attribute("aria-label")
                    if not listing_name: continue
                    
                    ActionChains(driver).move_to_element(link_to_process).perform()
                    time.sleep(random.uniform(*delays['short']))
                    driver.execute_script("arguments[0].click();", link_to_process)
                    header_selector = "h1.DUwDvf, h1.fontHeadlineLarge"
                    WebDriverWait(driver, 15).until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, header_selector), listing_name))
                    lead_data = extract_business_details(driver)
                    
                    business_address = lead_data.get("Full Business Address")
                    if business_address and business_address != "Not Found" and business_address in processed_addresses:
                        update_callback(f"  -> Duplicate found (already in CSV): {lead_data.get('Business Name')}. Skipping.")
                        continue
                        
                    writer.writerow(lead_data)
                    update_callback(f"  -> Lead #{len(processed_addresses) + 1}: {lead_data.get('Business Name', 'N/A')}")
                    leads_found_this_run += 1
                    if business_address and business_address != "Not Found":
                        processed_addresses.add(business_address)
                except StaleElementReferenceException:
                    update_callback("  -> Stale element detected. Re-evaluating page.")
                    processed_gmaps_link_count = 0
                    continue
                except Exception as e:
                    update_callback(f"  -> An unexpected error occurred: {e}")
                    continue
                if leads_found_this_run >= target_leads: break
    except Exception as e:
        update_callback(f"\nAn unexpected error occurred in the main process: {e}")
    finally:
        if driver: driver.quit()
        update_callback("\nScraping Session Finished.")