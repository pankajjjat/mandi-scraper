import requests
import csv
import os
import sys
import argparse
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import time

# Load environment variables
load_dotenv()

# Constants
API_ENDPOINT = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
DEFAULT_LIMIT = 1000  # Records per page

STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", 
    "Haryana", "Himachal Pradesh", "Jammu and Kashmir", "Jharkhand", "Karnataka", "Kerala", 
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", 
    "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", 
    "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands", "Chandigarh", 
    "Dadra and Nagar Haveli", "Daman and Diu", "Lakshadweep", "Delhi", "Puducherry"
]

def scrape_marketing_board_web():
    """
    Scrapes the Agmarknet website using Playwright.
    """
    url = "https://agmarknet.gov.in/PriceAndArrivals/DatewiseCommodityReport.aspx"
    
    print(f"Launching browser to scrape {url}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, timeout=60000)
            print("Page loaded. Validating content...")
            page.wait_for_load_state("networkidle")
            
            try:
                page.click("input[type='submit']", timeout=5000)
                print("Clicked Submit button...")
                page.wait_for_load_state("networkidle")
            except:
                print("No obvious submit button found or clickable immediately.")

            print("Looking for data table...")
            table_selector = "table" 
            page.wait_for_selector(table_selector, timeout=10000)
            
            html = page.content()
            dfs = pd.read_html(html)
            
            if dfs:
                df = max(dfs, key=len)
                print(f"Found table with {len(df)} rows.")
                filename = f"mandi_prices_web_scraped_{datetime.now().strftime('%Y%m%d')}.csv"
                df.to_csv(filename, index=False)
                print(f"Saved scraped data to {filename}")
                return df
            else:
                print("No tables found in the page content.")
                return None
                
        except Exception as e:
            print(f"Web scraping failed: {e}")
            return None
        finally:
            browser.close()

def get_api_key():
    """Retrieves API key from environment variable or user input."""
    api_key = os.getenv("DATA_GOV_IN_API_KEY")
    if not api_key:
        print("API Key not found in environment variables.")
        api_key = input("Please enter your data.gov.in API Key: ").strip()
    return api_key

def fetch_data(api_key, commodity=None, state=None, district=None, from_date=None, to_date=None, limit=DEFAULT_LIMIT):
    """
    Fetches data from Agmarknet API with optional filters.
    
    Args:
        api_key (str): The API key.
        commodity (str): Filter by crop/commodity name.
        state (str): Filter by state name.
        district (str): Filter by district name.
        from_date (datetime): Start date for filtering.
        to_date (datetime): End date for filtering.
        limit (int): Records per page.
    """
    all_records = []
    offset = 0
    
    print("Starting data fetch...")
    
    # Normalize dates to remove time component for comparison
    if from_date:
        from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)
    if to_date:
        to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999) # Set to end of day for inclusive comparison

    if commodity: print(f"Filter: Commodity='{commodity}'")
    if state: print(f"Filter: State='{state}'")
    if district: print(f"Filter: District='{district}'")
    if from_date: print(f"Filter: From Date='{from_date.strftime('%d/%m/%Y')}'")
    if to_date: print(f"Filter: To Date='{to_date.strftime('%d/%m/%Y')}'")

    while True:
        params = {
            "api-key": api_key,
            "format": "json",
            "limit": limit,
            "offset": offset
        }
        
        # Apply API-side filters
        if commodity:
            params["filters[commodity]"] = commodity
        if state:
            params["filters[state]"] = state
        if district:
            params["filters[district]"] = district

        try:
            response = requests.get(API_ENDPOINT, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "records" not in data:
                print("Error: 'records' key not found in response. Check API Key or limit.")
                # print(f"Response: {data}") # Debugging
                break
            
            records = data["records"]
            if not records:
                break  # No more data
            
            # Date Filtering (Client-side)
            # The API returns date as "DD/MM/YYYY" string.
            filtered_records = []
            
            for record in records:
                try:
                    record_date_str = record.get("arrival_date", "")
                    if not record_date_str:
                        # Decide whether to keep or skip records without dates. 
                        # Assuming we keep them if no date filter is applied, skip if it is.
                        if from_date or to_date:
                            continue
                        else:
                            filtered_records.append(record)
                            continue

                    record_date = datetime.strptime(record_date_str, "%d/%m/%Y")
                    
                    if from_date and record_date < from_date:
                        continue
                    if to_date and record_date > to_date:
                        continue
                    
                    filtered_records.append(record)
                    
                except ValueError:
                    print(f"Warning: Could not parse date '{record_date_str}'")
                    # If date parsing fails, similar logic to missing date
                    if not (from_date or to_date):
                         filtered_records.append(record)

            all_records.extend(filtered_records)
            print(f"Fetched {len(records)} raw API records. Kept {len(filtered_records)} after date filtering. Total Kept: {len(all_records)}")
            
            # Check total available API records to see if we're done fetching
            # Note: "total" in response refers to TOTAL MATCHING API FILTERS (commodity/state/district),
            # NOT including our client-side date filter.
            if "total" in data:
                 total_api_matches = int(data["total"])
                 # calculate how many raw records we have processed (offset + current batch)
                 records_processed = offset + len(records)
                 
                 if records_processed >= total_api_matches:
                     print("Fetched all matching API records.")
                     break

            offset += limit
            
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break

    return all_records

def save_to_csv(records, filename="mandi_prices_master.csv"):
    """Saves the list of records to a CSV file."""
    if not records:
        print("No records to save.")
        return

    print(f"Saving {len(records)} records to {filename}...")
    
    # Using pandas for easy CSV handling and potential future data manipulation
    df = pd.DataFrame(records)
    
    # Save to CSV
    try:
        df.to_csv(filename, index=False)
        print(f"Successfully saved data to {filename}")
    except Exception as e:
        print(f"Error saving CSV: {e}")

def parse_date(date_str):
    """Helper to parse date arguments."""
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: '{date_str}'. Use DD/MM/YYYY")

def main():
    parser = argparse.ArgumentParser(description="Scrape Mandi Prices with filters.")
    
    parser.add_argument("--commodity", "-c", help="Filter by Commodity/Crop (e.g., 'Wheat', 'Potato')")
    parser.add_argument("--state", "-s", help="Filter by State (e.g., 'Punjab')")
    parser.add_argument("--district", "-d", help="Filter by District (e.g., 'Agra')")
    parser.add_argument("--from-date", type=parse_date, help="Start Date (DD/MM/YYYY)")
    parser.add_argument("--to-date", type=parse_date, help="End Date (DD/MM/YYYY)")
    parser.add_argument("--output", "-o", default="mandi_prices_master.csv", help="Output CSV filename")

    args = parser.parse_args()

    print("=== Agmarknet Mandi Price Scraper ===")
    api_key = get_api_key()
    
    if not api_key:
        print("API Key not provided. Skipping API fetch.")
        records = []
    else:
        records = []
        try:
            if not (args.commodity or args.state or args.district):
                print("No filters provided. Initiating FULL SCAN by State to ensure complete data (bypassing 10k limit)...")
                all_state_records = []
                for state in STATES:
                    print(f"\n--- Fetching for State: {state} ---")
                    state_records = fetch_data(
                        api_key, 
                        commodity=args.commodity, 
                        state=state, 
                        district=args.district,
                        from_date=args.from_date,
                        to_date=args.to_date
                    )
                    all_state_records.extend(state_records)
                    # Optional: Save intermediate progress?
                    # valid: for now we just hold in memory or could append.
                records = all_state_records
            else:
                records = fetch_data(
                    api_key, 
                    commodity=args.commodity, 
                    state=args.state, 
                    district=args.district,
                    from_date=args.from_date,
                    to_date=args.to_date
                )
        except KeyboardInterrupt:
            print("\n\n[!] Scraping interrupted by user.")
            if 'all_state_records' in locals() and all_state_records:
                print(f"Saving {len(all_state_records)} records collected so far...")
                records = all_state_records
            elif 'records' in locals() and records:
                 print(f"Saving {len(records)} records collected so far...")
            else:
                 print("No records collected yet.")
                 sys.exit(0)
    
    if records:
        save_to_csv(records, filename=args.output)
        print("Scraping completed.")
    else:
        print("No data found from API.")
        choice = input("Would you like to try web scraping agmarknet.gov.in instead? (y/n): ").lower()
        if choice == 'y':
            try:
                from scraper_web import scrape_marketing_board_web
                scrape_marketing_board_web()
            except ImportError:
                print("Web scraper module not found. Please check requirements.")
            except Exception as e:
                print(f"Web scraping failed: {e}")
        else:
            print("Exiting.")

if __name__ == "__main__":
    main()
