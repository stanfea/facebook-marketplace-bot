from helpers.scraper import Scraper
from helpers.csv_helper import get_data_from_csv
from helpers.listing_helper import update_listings
from logging.config import fileConfig
import logging
import time

logger = logging.getLogger('sLogger')
fileConfig('log.ini')


def loop():
    scraper = Scraper('https://facebook.com', headless=False, publish=True)

    # Add login functionality to the scraper
    scraper.add_login_functionality('https://facebook.com', 'svg[aria-label="Your profile"]', 'facebook')
    scraper.go_to_page('https://facebook.com/marketplace/you/selling')

    # Get data for item type listings from csvs/items.csv
    logger.info("processing items")
    item_listings = get_data_from_csv('items')
    if item_listings:
        # Publish all the items into the facebook marketplace
        update_listings(item_listings, 'item', scraper)


def main():
    while True:
        loop()
        logger.info("sleeping for 10 minutes")
        time.sleep(10*60)


if __name__ == '__main__':
    main()
