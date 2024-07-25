import requests
import pandas as pd
from bs4 import BeautifulSoup

from apartments.settings import NEMA_URL
from apartments.config import connection
from apartments.utils import insert_data
from apartments.log import logger


# NOTE:  NEMA Chicago default rent is 12 months
# fetch and parse the page

def fetch_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        html = response.text
        return html
    except requests.exceptions.RequestException as e:
        logger.error(f'Error fetching page: {e}')


def parse_page(html):
    soup = BeautifulSoup(html, 'lxml')
    listings = soup.find_all('div', class_='availabilities-list__item')
    logger.info(f'There are {len(listings)} available units at NEMA Chicago')

    return listings


def extract_unit_data(listing):
    try:
        unit = listing.find('div', class_='cell--unit').get_text(strip=True)
        return unit
    except AttributeError:
        logger.error("Error extracting unit data")
        return None


def extract_rooms_data(listing):
    try:
        rooms = listing.find('div', class_='cell--bet').get_text(strip=True)
        bedrooms, baths = rooms.split('/')
        return bedrooms, baths
    except AttributeError:
        logger.error("Error extracting rooms data")
        return None, None


def extract_sqft_data(listing):
    try:
        sqft = listing.find('div', class_='cell--size').get_text(strip=True)
        return sqft
    except AttributeError:
        logger.error("Error extracting sqft data")
        return None


def extract_rent_data(listing):
    try:
        rent = listing.find('div', class_='cell--minRent').get_text(strip=True)
        return rent
    except AttributeError:
        logger.error("Error extracting rent data")
        return None


def extract_availability_data(listing):
    try:
        available_date = listing.find('div', class_='cell--viewAvailability').get_text(strip=True)
        return available_date
    except AttributeError:
        logger.error("Error extracting availability data")
        return None


def extract_data(listings):
    data = []
    for ls in listings:
        unit = extract_unit_data(ls)
        bedrooms, baths = extract_rooms_data(ls)
        sqft = extract_sqft_data(ls)
        rent = extract_rent_data(ls)
        available_date = extract_availability_data(ls)

        logger.info(f'Unit: {unit}, Bedrooms: {bedrooms}, Baths: {baths}, Sqft: {sqft}, Rent: {rent}, Available: {available_date}')

        data.append({
            'Plan': '',
            'Unit': unit,
            'Bedrooms': bedrooms,
            'Baths': baths,
            'Sq_ft': sqft,
            'Rent': rent,
            'Availability': available_date,
            'Retrieved': pd.Timestamp.now()
        })

    df = pd.DataFrame(data)

    return df

def clean_data(df):
    df['Apartment'] = 'NEMA Chicago'
    df['Retrieved'] = pd.Timestamp.now()

    df['Unit'] = df['Unit'].str.replace('#', '').str.strip()
    df['Bedrooms'] = df['Bedrooms'].str.replace('Bed', '').str.replace('s', '')
    df['Beds'] = df['Bedrooms']
    df.loc[df['Bedrooms'].str.contains('Studio'), 'Beds'] = 0
    df['Baths'] = df['Baths'].str.replace('Bath', '').str.replace('s', '').str.strip()
    df['Sq_ft'] = df['Sq_ft'].str.replace('SQ.Ft', '').str.replace(',', '')
    df['Rent'] = df['Rent'].str.replace('$', '').str.replace('/mo', '').str.replace(',', '')
    df.loc[df['Availability'].str.contains('IMMEDIATE'), 'Availability'] = pd.Timestamp.now().date()
    df['Availability'] = pd.to_datetime(df['Availability'])

    df = df[['Apartment', 'Plan', 'Unit', 'Bedrooms','Beds', 'Baths', 'Sq_ft', 'Rent', 'Availability', 'Retrieved']]

    return df


def get_nema_listings():
    html = fetch_page(url=NEMA_URL)
    listings = parse_page(html)
    df = extract_data(listings)
    df = clean_data(df)
    print(df)
    insert_data(connection, df)
    return df


if __name__ == '__main__':
    df = get_nema_listings()
    df.to_csv(f'./output/apts/nema_{pd.Timestamp.now().date()}.csv', index=False)
