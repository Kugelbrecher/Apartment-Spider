from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

from apartments.apartments_com.apt_com import APT_INFO_LIST

def setup_driver(headless=False):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')
    service=Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scrape_apartments(apt_info):
    driver = setup_driver(headless=False)
    driver.get(apt_info['url'])

    try:
        div_element = driver.find_element(By.CSS_SELECTOR, "div[data-tab-content-id='all']")
        sections = div_element.find_elements(By.CLASS_NAME, 'hasUnitGrid')
        print(f"Found {len(sections)} sections with units.")

        columns = ['model', 'unit_number', 'price', 'beds', 'baths', 'sq_ft', 'availability']
        df = pd.DataFrame(columns=columns)

        for section in sections:
            units = section.find_elements(By.CSS_SELECTOR, 'li.unitContainer')
            for unit in units:
                data = {
                    'model': unit.get_attribute('data-model'),
                    'unit_number': unit.get_attribute('data-unit'),
                    'price': unit.get_attribute('data-maxrent'),
                    'beds': unit.get_attribute('data-beds'),
                    'baths': unit.get_attribute('data-baths'),
                    'sq_ft': unit.find_element(By.CSS_SELECTOR, 'div.sqftColumn span:nth-of-type(2)').text,
                    'availability': unit.find_element(By.CSS_SELECTOR, 'span.dateAvailable').text#.split('\n')[-1]
                }
                df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)

        file_name = apt_info['name'] + '.csv'
        df.to_csv(f'./output/apts/{file_name}', index=False)
        print(f"Data saved to {file_name}")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        driver.quit()


if __name__ == '__main__':
    for apt_info in APT_INFO_LIST:
        scrape_apartments(apt_info)
        time.sleep(5)
