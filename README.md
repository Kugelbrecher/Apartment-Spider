# Apartment Spider/Scraper

This project is designed to gather and analyze data from various apartment listing websites, providing a valuable resource for renters, landlords, and real estate investors. The collected data helps in making well-informed decisions regarding renting, buying, or selling properties, and offers insights into local rental market trends. Such insights could also be used to forecast future trends in the market. Here are some examples of websites offering information on rental market trends:
- [zillow](https://www.zillow.com/rental-manager/market-trends/chicago-il/?propertyTypes=apartment-condo)
- [apartmentlist](https://www.apartmentlist.com/rent-report/il/chicago)
- [rentcafe](https://www.rentcafe.com/average-rent-market-trends/us/il/chicago/)
- [rentmeter](https://www.rentometer.com/)


This initiative involves scraping apartment listings from individual property websites and saving the data to a local CSV file and a database for two primary uses:
1. Displaying current listings on a real estate website.
2. Analyzing trends within the rental market.

## Web Scraping
The current list of apartments being scraped includes:
- 1000M (this is a new apartment building in Chicago)
- Eleven30
- Eleven40
- ELLE
- Grand Central
- LINEA
- NEMA

Continue to scrape more apartment websites.

## Data Analysis
The analysis focuses on two main areas: availability and rent prices.

Availability analysis:
- Daily tracking of the number of available units per building.
- Daily tracking of available units by apartment type (e.g., studio, one-bedroom).
- Comparative analysis of listing frequencies to gauge demand.

Rent Analysis:
- Calculation of average and median rents both overall and segmented by building and apartment type.
- Analysis of rent trends over time for different categories.
- Rent pricing per square foot for comparative assessments.

## Marketing Initiatives
- Create a draft email template for communication with the marketing team.
- Develop simple HTML or Markdown content, or even a dashboard, to effectively display the gathered and analyzed data.
- Implement a feature to automate the sending of emails to the marketing team and agents, providing daily, weekly, or monthly reports.
