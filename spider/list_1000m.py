import pandas as pd
from io import StringIO
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from apartments.settings import M1000_URL
from apartments.config import connection
from apartments.utils import setup_driver, insert_data
from apartments.log import logger


# NOTE: 1000M default rent is 12 months, same rent for 24/36 months contract
# use selenium to fetch the page content
# read table tag content to get listings


def fetch_table(url=M1000_URL):
    driver = setup_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        table_element = wait.until(EC.visibility_of_element_located((By.ID, 'availability-table')))
        table = table_element.get_attribute('outerHTML')
        df = pd.read_html(StringIO(table))[0]
        logger.info(f"There are {df.shape[0]} available units at 1000M")
        return df
    except TimeoutException:
        logger.error(f"Timeout while waiting for the table element at {url}")
    except Exception as e:
        logger.error(f"Error during data extraction: {e}")
    finally:
        driver.quit()
    return None


def clean_data(df):
    df = df.drop(columns=['Unnamed: 7'])
    df = df.rename(columns={
        'Apt#': 'Unit',
        'Plan': 'Plan',
        'Beds': 'Beds',
        'Baths': 'Baths',
        'Size': 'Sq_ft',
        'Starting at': 'Rent',
        'Available': 'Availability'
    })

    df['Apartment'] = '1000M'
    df['Retrieved'] = pd.Timestamp.now()

    df['Unit'] = df['Unit'].str.replace('Apt #:', '').str.strip()
    df['Plan'] = df['Plan'].str.replace('Floor Plan:', '').str.strip()
    df['Bedrooms'] = df['Beds'].str.replace('Beds:', '').str.replace('Bed', '').str.strip()
    df['Beds'] = df['Bedrooms']
    df.loc[df['Bedrooms'].str.contains('Studio|Convertible'), 'Beds'] = 0
    df.loc[df['Bedrooms'].str.contains('Den'), 'Beds'] = 1.5
    df['Baths'] = df['Baths'].str.replace('Baths:', '').str.replace('Bath', '').str.strip()
    df['Sq_ft'] = df['Sq_ft'].str.replace('Size:', '').str.replace(',', '').str.replace('sf', '').str.strip()
    df['Rent'] = df['Rent'].str.replace('Price:', '').str.replace('$', '').str.replace(',', '').str.strip()
    df['Availability'] = df['Availability'].str.replace('Available:', '').str.strip()
    df.loc[df['Availability'].str.contains('Now'), 'Availability'] = pd.Timestamp.now().date()
    df['Availability'] = pd.to_datetime(df['Availability'])

    df = df[['Apartment', 'Plan', 'Unit', 'Bedrooms','Beds', 'Baths', 'Sq_ft', 'Rent', 'Availability', 'Retrieved']]

    return df


def get_1000m_listings():
    df = fetch_table()
    df = clean_data(df)
    print(df)
    insert_data(connection, df)
    return df


if __name__ == '__main__':
    df = get_1000m_listings()
    df.to_csv(f'./output/apts/1000m_{pd.Timestamp.now().date()}.csv', index=False)
