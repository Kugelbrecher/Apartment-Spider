import pandas as pd
from io import StringIO
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from settings import ELEVEN40_URL
from config import connection
from utils import setup_driver, insert_data
from log import logger


def get_floor_plans(url=ELEVEN40_URL):
    """Scrape floor plan data from the specified URL."""
    driver = setup_driver()
    driver.get(url)

    try:
        floor_plans = driver.find_elements(By.CLASS_NAME, 'floorplan-section')
        print(f'Total floor plans: {len(floor_plans)}')

        df = pd.DataFrame()
        for fp in floor_plans:
            df_section = extract_floor_plan_info(fp)
            df = pd.concat([df, df_section], ignore_index=True)
            print('-------------------')

    finally:
        driver.quit()

    return df


def extract_floor_plan_info(fp):
    """Extract information of a single floor plan."""
    fp_info = fp.find_element(By.CLASS_NAME, 'col-lg-8')
    plan = fp_info.text.split('\n')[0]
    rooms = fp_info.text.split('\n')[-1]
    print(f'Floor Plan: {plan}, Rooms: {rooms}')

    bedrooms, bathrooms = rooms.split('|')
    
    table = fp.find_element(By.TAG_NAME, 'table')
    hrefs = [a.get_attribute('href') for a in table.find_elements(By.TAG_NAME, 'a')]
    print(f'number of select links: {len(hrefs)}')

    df_section = pd.read_html(StringIO(table.get_attribute('outerHTML')))[0]
    df_section['Plan'] = plan
    df_section['Bedrooms'] = bedrooms.strip()
    df_section['Baths'] = bathrooms.strip()
    df_section['href'] = hrefs

    print(df_section)
    return df_section


def fetch_unit_details(link):
    """Fetch details of a unit from its link."""
    driver = setup_driver()
    try:
        driver.get(link)
        lease_info = driver.find_element(By.ID, 'divTermInfo')

        date_input = lease_info.find_element(By.ID, 'DateDiv').find_element(By.TAG_NAME, 'input')
        availability = date_input.get_attribute('value')

        rent_info = lease_info.find_element(By.ID, 'divPricingInfo').text
        rent = rent_info.split('\n')[1] if rent_info else None

        return availability, rent

    except NoSuchElementException as e:
        logger.error(f"Element not found: {e}")
        return None, None

    except Exception as e:
        logger.error(f"Error fetching unit details: {e}")
        return None, None

    finally:
        driver.quit()


def get_all_unit_details(df):
    """Fetch details for all units in the DataFrame."""
    availability_dates, twelve_month_rent = [], []
    for link in df['href'].tolist():
        availability, rent = fetch_unit_details(link)
        availability_dates.append(availability)
        twelve_month_rent.append(rent)
    
    df['Availability'] = availability_dates
    df['12_month_rent'] = twelve_month_rent
    return df


def clean_data(df):
    """Clean and prepare the DataFrame for database insertion."""
    df.drop(columns=['Action', 'href', 'Rent'], inplace=True)
    df.rename(columns={
        'Apartment': 'Unit',
        'Sq. Ft.': 'Sq_ft',
        '12_month_rent': 'Rent'
    }, inplace=True)

    df['Apartment'] = 'Eleven 40'
    df['Retrieved'] = pd.Timestamp.now()

    df['Unit'] = df['Unit'].str.replace('Apartment: #', '').str.strip()
    df['Sq_ft'] = df['Sq_ft'].str.replace('Sq. Ft.:', '').str.replace(',', '').str.strip()
    df['Bedrooms'] = df['Bedrooms'].str.replace('Bedroom', '').str.replace('s', '').str.strip()
    df['Beds'] = df['Bedrooms']
    df.loc[df['Bedrooms'].str.contains('Studio'), 'Beds'] = 0
    df['Baths'] = df['Baths'].str.replace('Bathroom', '').str.replace('s', '').str.strip()
    df['Rent'] = df['Rent'].str.replace('$', '').str.replace(',', '').str.strip()
    df['Availability'] = df['Availability'].str.replace('Available:', '').str.strip()
    df['Availability'] = pd.to_datetime(df['Availability'])


    df = df[['Apartment', 'Plan', 'Unit', 'Bedrooms', 'Beds', 'Baths', 'Sq_ft', 'Rent', 'Availability', 'Retrieved']]

    return df


def get_1140_listings():
    """Main function to scrape and process listings."""
    df = get_floor_plans()
    df = get_all_unit_details(df)
    df = clean_data(df)
    insert_data(connection, df)
    return df


if __name__ == '__main__':
    df = get_1140_listings()
    df.to_csv(f'./output/apts/1140_{pd.Timestamp.now().date()}.csv', index=False)
