from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
import os

ua = UserAgent()

def setup_driver(headless=True):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')
    options.add_argument(f'user-agent={ua.random}') # add user agent to pass bot detection, o.w. add click action
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver_path = ChromeDriverManager().install()
    service = Service(driver_path)
    
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def insert_data(conn, data):
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO availabilities (apartment, plan, unit, bedrooms, beds, baths, sqft, rent, available_date, retrieved)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    for _, row in data.iterrows():
        cursor.execute(insert_query, (
            row['Apartment'], row['Plan'], row['Unit'],
            row['Bedrooms'], row['Beds'], row['Baths'], 
            row['Sq_ft'], row['Rent'], row['Availability'], 
            row['Retrieved']
        ))
    conn.commit()
    cursor.close()
    print("Data inserted successfully into the database.")


if __name__ == '__main__':
    driver = setup_driver()