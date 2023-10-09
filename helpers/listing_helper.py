import datetime
import logging
import os
from helpers.history import history_load, history_save
from datetime import datetime

logger = logging.getLogger('sLogger')


# Remove and then publish each listing
def update_listings(listings, type, scraper):
    history = history_load()
    # If listings are empty stop the function
    if not listings:
        return

    # Check if listing is already listed and remove it then publish it like a new one if it has expired ttl
    for listing in listings:
        if listing['Description'] == "example":
            logger.info(f"skipping \"{listing['Title']}\" because Description is just \"example\"")
            continue

        title = listing['Title']
        ttl = int(listing['HoursTTL'])

        # check if listing exists
        listing_title_element = find_listing_by_title(title, scraper)
        now = datetime.now()
        if listing_title_element:
            if title in history:
                published_time = history[title]
                delta = now - published_time
                hours_delta = round(delta.seconds / 3600)
                if hours_delta < ttl:
                    logger.info(f"\"{title}\" has {ttl - hours_delta} hours to go")
                    continue
                else:
                    logger.info(f"\"{title}\" has expired republishing")
            else:
                # listing not in history database give it ttl hours to go
                logger.info(f"\"{title}\" already published but not found in history.yaml giving it {ttl} hours to go")
                history[title] = now
                history_save(history)
                continue
            remove_listing(listing_title_element, scraper)
        else:
            logger.info(f"\"{title}\" publishing for {ttl} hours")

        publish_listing(listing, type, scraper)
        title = listing['Title']
        history[title] = datetime.now()
        history_save(history)


def remove_listing(listing_title_element, scraper):
    listing_title_element.click()

    # Click on the delete listing button
    scraper.element_click('div[aria-label="Delete"]')

    # Click on confirm button to delete
    confirm_delete_selector = 'div[aria-label="Delete listing"] div[aria-label="Delete"][tabindex="0"]'
    if scraper.find_element(confirm_delete_selector, False, 3):
        scraper.element_click(confirm_delete_selector, True, 3)
    else:
        confirm_delete_selector = 'div[aria-label="Delete Listing"] div[aria-label="Delete"][tabindex="0"]'
        scraper.find_element(confirm_delete_selector, True, 3)
        scraper.element_click(confirm_delete_selector, True, 3)

    # Wait until the popup is closed
    scraper.element_wait_to_be_invisible('div[aria-label="Your Listing"]')
    return True


def get_user_id(scraper):
    scraper.go_to_page("https://www.facebook.com/profile")
    user_id = scraper.driver.current_url.split("?id=")[1]


def publish_listing(data, listing_type, scraper):
    # Click on create new listing button
    scraper.element_click('div[aria-label="Marketplace sidebar"] a[aria-label="Create new listing"]')
    # Choose listing type
    scraper.element_click('a[href="/marketplace/create/' + listing_type + '/"]')

    # Create string that contains all the image paths seperated by \n
    images_path = generate_multiple_images_path(data['Photos Folder'], data['Photos Names'])
    # Add images to the listing
    scraper.input_file_add_files('input[accept="image/*,image/heif,image/heic"]', images_path)

    add_fields(data, scraper, listing_type)

    scraper.element_send_keys('label[aria-label="Price"] input', data['Price'], wait_element_time=3)
    scraper.element_send_keys('label[aria-label="Description"] textarea', data['Description'], wait_element_time=3)

    groups = [group.strip() for group in data['Groups'].split(";") if group.strip() != ""]

    def set_location():
        element = scraper.element_send_keys('label[aria-label="Location"] input', data['Location'],
                                            exit_on_missing_element=False, wait_element_time=3)
        if element:
            scraper.element_click('ul[role="listbox"] li:first-child > div', wait_element_time=3)
            return True
        return False

    location_set = set_location()
    next_button_selector = 'div [aria-label="Next"] > div'
    next_button = scraper.find_element(next_button_selector, False, 3)
    if next_button:
        scraper.element_click(next_button_selector)
        # Go to the next step
        if not location_set:
            location_set = set_location()
            if not location_set:
                raise Exception(f"failed to set location to {data['Location']}")
            scraper.element_click(next_button_selector, wait_element_time=3)
        # Add listing to multiple groups
        groups = add_listing_to_groups_with_shops(groups, scraper)

    if not scraper.publish:
        return

    # Publish the listing
    scraper.element_click('div[aria-label="Publish"]:not([aria-disabled])')

    # next_button = scraper.find_element(next_button_selector, False, 3)
    # if not next_button:
    #     post_listing_to_groups_without_shop(data, groups, scraper)


def generate_multiple_images_path(path, images):
    return "\n".join([os.path.join(path, image) for image in images.split(";") if image])


def add_fields(data, scraper, type):
    if type == "vehicle":
        return add_fields_for_vehicle(data, scraper)
    elif type == "item":
        return add_fields_for_item(data, scraper)
    else:
        raise Exception(f"Unknown type \"{type}\"")


# Add specific fields for listing from type vehicle
def add_fields_for_vehicle(data, scraper):
    # Expand vehicle type select
    scraper.element_click('label[aria-label="Vehicle type"]')
    # Select vehicle type
    scraper.element_click_by_xpath('//span[text()="' + data['Vehicle Type'] + '"]')

    # Scroll to years select
    scraper.scroll_to_element('label[aria-label="Year"]')
    # Expand years select
    scraper.element_click('label[aria-label="Year"]')
    scraper.element_click_by_xpath('//span[text()="' + data['Year'] + '"]')

    scraper.element_send_keys('label[aria-label="Make"] input', data['Make'])
    scraper.element_send_keys('label[aria-label="Model"] input', data['Model'])

    # Scroll to mileage input
    scraper.scroll_to_element('label[aria-label="Mileage"] input')
    # Click on the mileage input
    scraper.element_send_keys('label[aria-label="Mileage"] input', data['Mileage'])

    # Expand fuel type select
    scraper.element_click('label[aria-label="Fuel type"]')
    # Select fuel type
    scraper.element_click_by_xpath('//span[text()="' + data['Fuel Type'] + '"]')


# Add specific fields for listing from type item
def add_fields_for_item(data, scraper):
    scraper.element_send_keys('label[aria-label="Title"] input', data['Title'])

    # Scroll to "Category" select field
    scraper.scroll_to_element('label[aria-label="Category"]')
    # Expand category select
    scraper.element_click('label[aria-label="Category"]')
    # Select category
    if not scraper.element_click_by_xpath('//span[text()="' + data['Category'] + '"]', exit_on_missing_element=False,
                                          wait_element_time=3):
        # newer marketplace lets you search categories
        scraper.element_delete_text('label[aria-label="Category"]')
        scraper.element_send_keys('label[aria-label="Category"]', data['Category'])
        if not scraper.element_click_by_xpath('//span[text()="' + data['Category'] + '"]',
                                              exit_on_missing_element=False, wait_element_time=3):
            raise Exception(f"Could not find category {data['Category']}")

    # Expand category select
    scraper.element_click('label[aria-label="Condition"]')
    # Select category
    condition = data['Condition'].replace("–", "-")
    if not scraper.element_click_by_xpath('//span[@dir="auto"][text()="' + condition + '"]',
                                          exit_on_missing_element=False, wait_element_time=3):
        # other version of marketplace uses big hyphens
        condition = condition.replace("-", "–")
        if not scraper.element_click_by_xpath('//span[@dir="auto"][text()="' + condition + '"]',
                                              exit_on_missing_element=False, wait_element_time=3):
            raise Exception(f"Could not find condition {condition}")

    element = scraper.find_element('label[aria-label="Brand"]', exit_on_missing_element=False, wait_element_time=3)
    if element:
        scraper.element_send_keys('label[aria-label="Brand"] input', data['Brand'])


def add_listing_to_groups_with_shops(groups, scraper):
    if not groups:
        return []
    remaining_groups = []
    # Post in different groups
    for group_name in groups:
        if not scraper.element_click_by_xpath('//span[text()="' + group_name + '"]', True, False, 5):
            remaining_groups.append(group_name)
    return remaining_groups


def post_listing_to_groups_without_shop(data, groups, scraper):
    logger.info("post_listing_to_groups_without_shop" + ", ".join(groups))
    if not groups:
        return

    title_element = find_listing_by_title(data, scraper)
    # If there is no add with this title do nothing
    if not title_element:
        return
    search_input_selector = '[aria-label="Search for groups"]'

    # Post in different groups
    for group_name in groups:
        # Click on the Share button to the listing that we want to share
        scraper.element_click('[aria-label="' + data['Title'] + '"] + div [aria-label="Share"]')
        # Click on the Share to a group button
        scraper.element_click_by_xpath('//span[text()="Share to a group"]')

        # Remove whitespace before and after the name
        group_name = group_name.strip()

        # Remove current text from this input
        scraper.element_delete_text(search_input_selector)
        # Enter the title of the group in the input for search
        scraper.element_send_keys(search_input_selector, group_name)

        scraper.element_click_by_xpath('//span[text()="' + group_name + '"]')

        if scraper.find_element('[aria-label="Create a public post…"]', False, 3):
            scraper.element_send_keys('[aria-label="Create a public post…"]', data['Description'])
        elif scraper.find_element('[aria-label="Write something..."]', False, 3):
            scraper.element_send_keys('[aria-label="Write something..."]', data['Description'])

        scraper.element_click('[aria-label="Post"]:not([aria-disabled])')
        # Wait till the post is posted successfully
        scraper.element_wait_to_be_invisible('[role="dialog"]')
        scraper.element_wait_to_be_invisible('[aria-label="Loading...]"')
        scraper.find_element_by_xpath('//span[text()="Shared to your group."]', False, 10)


def find_listing_by_title(title, scraper, exit_on_missing_element=False):
    searchInput = scraper.find_element('input[placeholder="Search your listings"]', False, 10)
    # Search input field is not existing
    if not searchInput:
        return None

    # Clear input field for searching listings before entering title
    scraper.element_delete_text('input[placeholder="Search your listings"]')
    # Enter the title of the listing in the input for search
    scraper.element_send_keys('input[placeholder="Search your listings"]', title)
    return scraper.find_element_by_xpath('//span[text()="' + title + '"]', exit_on_missing_element, 10)
