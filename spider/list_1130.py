import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from apartments.settings import ELEVEN30_URL
from apartments.config import connection
from apartments.utils import setup_driver, insert_data
from apartments.log import logger

# NOTE: designed by RentCafe
# use selenium to fetch the floor plans with available units
# find SEE LEASE INFORMATION button href in each unit, redirect and read html to get 12-month rent

def fetch_listings(url=ELEVEN30_URL):
    """
    Fetch all floor plans within the page, then find all listings from each floor plan div.
    """
    driver = setup_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        floor_plans = wait.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, 'units-list')))
        logger.info(f"There are {len(floor_plans)} floor plans at 1130")

        data = []
        for fp in floor_plans:
            try:
                # floor plan in section title, including bed/bath count
                plan = fp.find_element(By.TAG_NAME, 'h3').text

                # available units
                fp_listings = fp.find_element(By.CLASS_NAME, 'table-body')
                units = fp_listings.find_elements(By.CLASS_NAME, 'unit-item')
                logger.info(f"There are {len(units)} units available for {plan}")

                for unit in units:
                    try:
                        # basic unit info
                        unit_infos = unit.find_elements(By.CLASS_NAME, 'col-2')
                        unit_num = unit_infos[0].find_element(By.TAG_NAME, 'span').text
                        sq_ft = unit_infos[1].text
                        rent_range = unit_infos[2].text
                        availability = unit_infos[3].text
                        unit_info_list = [plan, unit_num, sq_ft, rent_range, availability]
                        # button href
                        link = unit.find_elements(By.TAG_NAME, 'a')[-1].get_attribute('href')

                        unit_info_list.append(link)
                        logger.info(f"Unit {unit_num}, {sq_ft}, {rent_range}, {availability}, {link}")
                        data.append(unit_info_list)

                    except Exception as unit_exception:
                        logger.error(f"Error processing unit: {unit_exception}")
                        continue

            except Exception as plan_exception:
                logger.error(f"Error processing floor plan: {plan_exception}")
                continue

        df = pd.DataFrame(data, columns=['Plan', 'Unit', 'Sq_ft', 'Rent_range', 'Availability', 'href'])

        return df

    except Exception as e:
        logger.error(f"Error fetching listings: {e}")

    finally:
        driver.quit()


def get_unit_details(df):
    unit_links = df['href'].tolist()

    twelve_month_rent = []
    for link in unit_links:
        driver = setup_driver()
        driver.get(link)
        try:
            rent_element = driver.find_element(By.XPATH, '//*[@id="CSFlipCard"]/div/div[1]/div[2]/div[1]/div/span[1]')
            rent = rent_element.text.replace('$', '').replace(',', '')
        except NoSuchElementException:
            rent = None

        twelve_month_rent.append(rent)
        driver.quit()

    df['Rent'] = twelve_month_rent

    return df


def clean_data(df):
    df['Apartment'] = 'Eleven 30'
    df['Retrieved'] = pd.Timestamp.now()

    df['rooms'] = df['Plan'].apply(lambda x: x.split(' ')[-1])
    df['rooms'] = df['rooms'].str.replace('(', '').str.replace(')', '')
    df['Bedrooms'] = df['rooms'].apply(lambda x: x.split('/')[0])
    df['Beds'] = df['Bedrooms'].str.replace('BR', '').str.strip()
    df['Beds'] = df['Beds'].apply(lambda x: 0 if x == 'Studio' else x)
    df['Baths'] = df['rooms'].apply(lambda x: x.split('/')[-1])
    df['Baths'] = df['Baths'].str.replace('BA', '').str.strip()
    df['Baths'] = df['Baths'].apply(lambda x: 1 if x == 'Studio' else x)
    df.loc[df['Availability'].str.contains('Now'), 'Availability'] = pd.Timestamp.now().date()
    df['Availability'] = pd.to_datetime(df['Availability'])

    df = df[['Apartment', 'Plan', 'Unit', 'Bedrooms','Beds', 'Baths', 'Sq_ft', 'Rent', 'Availability', 'Retrieved']]

    return df


def get_1130_listings():
    df = fetch_listings()
    df = get_unit_details(df)
    df = clean_data(df)
    insert_data(connection, df)
    return df


if __name__ == '__main__':
    df = get_1130_listings()
    df.to_csv(f'./output/apts/1130_{pd.Timestamp.now().date()}.csv', index=False)
