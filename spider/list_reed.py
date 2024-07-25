import pandas as pd
import time
from io import StringIO
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from apartments.settings import REED_URL
from apartments.config import connection
from apartments.utils import setup_driver, insert_data
from apartments.log import logger

# NOTE:
# first page list all floor plans, click each floor plan to get available units, but they are on the same page
# use select button to redirect to leasing info page to get 12 month rent

def get_unit_details(url=REED_URL):
    # this is irrelevant to get floor plans, because they lie in the same html element
    driver = setup_driver()
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    floor_plans = soup.find_all('div', class_='availability-mdl js-availability-mdl')
    print(f'number of floor plans: {len(floor_plans)}')

    df = pd.DataFrame()
    for fp in floor_plans:
        # fp information:
        fp_info = fp.find('div', class_='availability-mdl__header')
        plan = fp_info.find('h5').text
        print(f'plan: {plan}')
        p_tags = fp_info.find_all('p')
        bedrooms = p_tags[0].text
        bedrooms = bedrooms.replace('Bed', '').strip()
        baths = p_tags[1].text
        baths = baths.replace('Bath', '').strip()
        sq_ft = p_tags[2].text
        print(f'bedrooms: {bedrooms}, baths: {baths}, sq_ft: {sq_ft}')

        # available units using pd read html
        fp_listings = fp.find('div', class_='availability-mdl__table u-bg-black')
        fp_df = pd.read_html(StringIO(str(fp_listings)))[0]
        # print(fp_df)

        # get the href in a tag from the last column
        hrefs = fp_listings.find_all('a')
        hrefs = [a['href'] for a in hrefs]

        # add plan, bedrooms, baths as new columns to df
        fp_df['Plan'] = plan
        fp_df['Bedrooms'] = bedrooms
        fp_df['Baths'] = baths
        fp_df['SQFT'] = sq_ft
        fp_df['href'] = hrefs

        df = pd.concat([df, fp_df], ignore_index=True)

    print(df)

    driver.quit()

    return df


def fetch_unit_details(link):
    """Fetch details of a unit from its link."""
    driver = setup_driver()
    try:
        driver.get(link)
        lease_info = driver.find_element(By.ID, 'divTermInfo')

        # TODO: default date is not earliest available date, so we need to pick the date to see 12 month rent
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
    
    # df['Availability'] = availability_dates # cannot use this cuz all as current date
    df['12_month_rent'] = twelve_month_rent
    return df


def clean_data(df):
    df.drop(columns=['View', 'href', 'Rent', 'Date Available'], inplace=True)
    df.rename(columns={
        'SQFT': 'Sq_ft',
        '12_month_rent': 'Rent'
    }, inplace=True)

    df['Apartment'] = 'Reed'
    df['Retrieved'] = pd.Timestamp.now()

    df['Rent'] = df['Rent'].str.replace('$', '').str.replace(',', '').str.strip()#.astype(float)
    df['SQFT'] = df['SQFT'].str.replace('SF', '').str.replace(',', '').str.strip()
    df['Availability'] = df['Availability'].str.replace('Available ', '').str.strip()
    df['Beds'] = df['Bedrooms']
    df.loc[df['Bedrooms'].str.contains('Studio|Convertible'), 'Beds'] = 0

    df['Availability'] = df['Availability'].str.replace('Available:', '').str.strip()
    df['Availability'] = pd.to_datetime(df['Availability'])

    df = df[['Apartment', 'Plan', 'Unit', 'Bedrooms','Beds', 'Baths', 'Sq_ft', 'Rent', 'Availability', 'Retrieved']]

    return df


def get_reed_listings():
    df = get_unit_details()
    df = get_all_unit_details(df)
    # df = clean_data(df)
    # insert_data(connection, df)
    return df


if __name__ == '__main__':
    df = get_reed_listings()
    df.to_csv(f'./output/apts/reed_{pd.Timestamp.now().date()}.csv', index=False)