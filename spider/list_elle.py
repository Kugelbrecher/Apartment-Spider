import pandas as pd
from io import StringIO
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from apartments.settings import ELLE_URL
from apartments.config import connection
from apartments.utils import setup_driver, insert_data
from apartments.log import logger

# NOTE:
# same logo with grand central
# find all floor plans
# use available button to get to unit listing page
# use select button to get to leasing info page

def get_floor_plans(url=ELLE_URL):
    # find all listed floor plans
    driver = setup_driver()
    driver.get(url)

    # 1. find section of all floor plans
    floor_plan_container = driver.find_element(By.ID, 'floorplans-container')
    floor_plans = floor_plan_container.find_elements(By.CLASS_NAME, 'fp-container')
    logger.info(f'There are {len(floor_plans)} floor plans for Elle.')

    data = []
    for fp in floor_plans:
        # find floor plan info by class name
        fp_info = fp.find_element(By.CLASS_NAME, 'card-header')
        fp_info_list = fp_info.text.split('\n')
        # print(fp_info_list)
        fp_link = fp.find_element(By.CLASS_NAME, 'card-body')
        a_tags = fp_link.find_elements(By.TAG_NAME, 'a')[-2].get_attribute('href')
        # print(a_tags)
        fp_info_list.append(a_tags)
        data.append(fp_info_list)

    df = pd.DataFrame(data, columns=['Plan', 'Bedrooms', 'Baths', 'Sq_ft', 'link'])

    driver.quit()

    return df


def get_unit_listing(df):
    fp_links = df['link'].tolist()
    fp_links = [link for link in fp_links if 'https://www.theellechicago.com/floorplans/' in link]
    print(f'Number of floor plan links: {len(fp_links)}')

    listing_df = pd.DataFrame()
    for link in fp_links:
        driver = setup_driver()
        driver.get(link)

        section = driver.find_element(By.CLASS_NAME, 'floorplan-section')

        # read floor plan details
        h2 = section.find_element(By.TAG_NAME, 'h2')
        plan = h2.text
        print(plan)
        spans = section.find_elements(By.TAG_NAME, 'span')[:2]
        bedrooms = spans[0].text
        baths = spans[1].text
        print(f'bedrooms: {bedrooms}, baths: {baths}')

        # read listing table
        table_div = section.find_element(By.CLASS_NAME, 'table-responsive')

        unit_href = []
        rows = table_div.find_elements(By.TAG_NAME, 'tr')
        for row in rows[1:]:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if cells:
                last_cell = cells[-1]
                a_tag = last_cell.find_element(By.TAG_NAME, 'a')
                link = a_tag.get_attribute('href')
                print(f'Link in last column: {link}')
                unit_href.append(link)

        table_html = table_div.get_attribute('outerHTML')
        table = pd.read_html(StringIO(table_html))[0]
        table['Plan'] = plan
        table['Bedrooms'] = bedrooms
        table['Baths'] = baths
        table['href'] = unit_href

        listing_df = pd.concat([listing_df, table], ignore_index=True)

        driver.quit()

    return listing_df


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
    df.drop(columns=['Action', 'href', 'Rent', 'Date Available'], inplace=True)
    df.rename(columns={
        'Apartment': 'Unit',
        'Sq. Ft.': 'Sq_ft',
        '12_month_rent': 'Rent'
    }, inplace=True)

    df['Apartment'] = 'ELLE'
    df['Retrieved'] = pd.Timestamp.now()

    df['Unit'] = df['Unit'].str.replace('Apartment: #', '').str.strip()
    df['Sq_ft'] = df['Sq_ft'].str.replace('Sq. Ft.:', '').str.replace(',', '').str.strip()
    df['Bedrooms'] = df['Bedrooms'].str.replace('Bedroom', '').str.replace('s', '').str.strip()
    df['Beds'] = df['Bedrooms'].apply(lambda x: 0 if x == 'Studio' else x)
    df['Baths'] = df['Baths'].str.replace('Bathroom', '').str.replace('s', '').str.strip()
    df['Rent'] = df['Rent'].str.replace('$', '').str.replace(',', '').str.strip()
    df['Availability'] = df['Availability'].str.replace('Available:', '').str.strip()
    df['Availability'] = pd.to_datetime(df['Availability'])

    df = df[['Apartment', 'Plan', 'Unit', 'Bedrooms','Beds', 'Baths', 'Sq_ft', 'Rent', 'Availability', 'Retrieved']]

    return df


def get_elle_listings():
    df = get_floor_plans()
    df = get_unit_listing(df)
    df = get_all_unit_details(df)
    df = clean_data(df)
    insert_data(connection, df)
    return df


if __name__ == '__main__':
    df = get_elle_listings()
    df.to_csv(f'./output/apts/elle_{pd.Timestamp.now().date()}.csv', index=False)