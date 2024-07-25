import pandas as pd
from io import StringIO
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

from settings import LINEA_URL
from config import connection
from utils import setup_driver, insert_data
from log import logger

# NOTE: designed by Willow Bridge, same layout as 1000M
# use selenium to fetch the page content
# read table tag content to get listings
# find LEASE button href in each unit, redirect and read html to get 12-month rent

def fetch_table(url=LINEA_URL):
    driver = setup_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        table_element = wait.until(EC.visibility_of_element_located((By.ID, 'availability-table')))
        table_html = table_element.get_attribute('outerHTML')
        df = pd.read_html(StringIO(table_html))[0]

        # find the LEASE button href in each unit
        soup = BeautifulSoup(table_html, 'html.parser')
        rows = soup.find_all('tr')
        hrefs = [row.find_all('td')[-1].find_all('a')[-1]['href'] 
                 if row.find_all('td')[-1].find_all('a') else None for row in rows[1:]]
        df['href'] = hrefs

        logger.info(f"There are {df.shape[0]} available units at LINEA")
        return df
    except TimeoutException:
        logger.error(f"Timeout while waiting for the table element at {url}")
    except Exception as e:
        logger.error(f"Error fetching the page: {e}")
    finally:
        driver.quit()
    return None


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
    availability_dates, twelve_month_rent = [], []
    for link in df['href'].tolist():
        availability, rent = fetch_unit_details(link)
        availability_dates.append(availability)
        twelve_month_rent.append(rent)
    
    df['Availability'] = availability_dates
    df['12_month_rent'] = twelve_month_rent
    return df


def clean_data(df):
    df = df.drop(columns=['Unnamed: 7', 'Starting at', 'href'])
    df = df.rename(columns={
        'Apt#': 'Unit',
        'Plan': 'Plan',
        'Beds': 'Beds',
        'Baths': 'Baths',
        'Size': 'Sq_ft',
        '12_month_rent': 'Rent'
    })

    df['Apartment'] = 'LINEA'
    df['Retrieved'] = pd.Timestamp.now()

    df['Unit'] = df['Unit'].str.replace('Apt #:', '').str.strip()
    df['Plan'] = df['Plan'].str.replace('Floor Plan:', '').str.strip()
    df['Bedrooms'] = df['Beds'].str.replace('Beds:', '').str.replace('Bed', '').str.strip()
    df['Beds'] = df['Bedrooms']
    df.loc[df['Bedrooms'].str.contains('Studio|Convertible'), 'Beds'] = 0
    df['Baths'] = df['Baths'].str.replace('Baths:', '').str.replace('Bath', '').str.strip()
    df['Sq_ft'] = df['Sq_ft'].str.replace('Size:', '').str.replace(',', '').str.replace('sf', '').str.strip()
    df['Rent'] = df['Rent'].str.replace('Price:', '').str.replace('$', '').str.replace(',', '').str.strip()
    df['Availability'] = df['Availability'].astype(str).str.replace('Available:', '').str.strip() # why says df object does not have str
    df['Availability'] = pd.to_datetime(df['Availability'])

    df = df[['Apartment', 'Plan', 'Unit', 'Bedrooms','Beds', 'Baths', 'Sq_ft', 'Rent', 'Availability', 'Retrieved']]

    return df


def get_linea_listings():
    df = fetch_table()
    df = get_all_unit_details(df)
    df = clean_data(df)
    insert_data(connection, df)
    return df


if __name__ == '__main__':
    df = get_linea_listings()
    df.to_csv(f'./output/apts/linea_{pd.Timestamp.now().date()}.csv', index=False)
