import os
import pickle
import time
import random
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import InvalidArgumentException
from selenium.common.exceptions import ElementClickInterceptedException
import logging
import sys

logger = logging.getLogger('sLogger')


class Scraper:
    # This time is used when we are waiting for element to get loaded in the html
    wait_element_time = 30

    # In this folder we will save cookies from logged in users
    cookies_folder = 'cookies' + os.path.sep

    def __init__(self, url, headless=True, publish=True):
        self.url = url
        self.headless = headless
        self.publish = publish

    # Automatically close driver on destruction of the object
    def __del__(self):
        try:
            self.driver.close()
        except:
            pass

    def restart_driver(self, headless=True):
        if hasattr(self, 'driver'):
            self.driver.close()
        self.setup_driver_options(headless=headless)
        self.setup_driver()

    # Add these options in order to make chrome driver appear as a human instead of detecting it as a bot
    # Also change the 'cdc_' string in the chromedriver.exe with Notepad++ for example with 'abc_' to prevent detecting it as a bot
    def setup_driver_options(self, headless=True):
        self.driver_options = Options()

        arguments = [
            '--disable-blink-features=AutomationControlled',
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        ]
        if headless:
            arguments.append("--headless=new")

        experimental_options = {
            'excludeSwitches': ['enable-automation', 'enable-logging'],
            'prefs': {'profile.default_content_setting_values.notifications': 2}
        }

        for argument in arguments:
            self.driver_options.add_argument(argument)

        for key, value in experimental_options.items():
            self.driver_options.add_experimental_option(key, value)

    # Setup chrome driver with predefined options
    def setup_driver(self):
        chrome_driver_path = ChromeDriverManager().install()
        self.driver = webdriver.Chrome(service=ChromeService(chrome_driver_path), options=self.driver_options)
        self.driver.get(self.url)
        self.driver.maximize_window()

    # Add login functionality and load cookies if there are any with 'cookies_file_name'
    def add_login_functionality(self, login_url, is_logged_in_selector, cookies_file_name):
        self.login_url = login_url
        self.is_logged_in_selector = is_logged_in_selector
        self.cookies_file_name = cookies_file_name + '.pkl'
        self.cookies_file_path = self.cookies_folder + self.cookies_file_name

        # Check if there is a cookie file saved
        if self.is_cookie_file():
            self.restart_driver(headless=self.headless)
            # Load cookies
            self.load_cookies()

            # Check if user is logged in after adding the cookies
            is_logged_in = self.is_logged_in(5)
            if is_logged_in:
                return
        # restart with gui so user can login
        self.restart_driver(headless=False)
        # Wait for the user to log in with maximum amount of time 5 minutes
        logger.info(
            'Please login manually in the browser and after that you will be automatically loged in with cookies. Note that if you do not log in for five minutes, the program will turn off.')
        is_logged_in = self.is_logged_in(300)

        # User is not logged in so exit from the program
        if not is_logged_in:
            logger.error("user not logged in please restart program")
            time.sleep(10)
            sys.exit(1)
        # User is logged in so save the cookies
        self.save_cookies()
        if self.headless:
            self.restart_driver(headless=True)

    # Check if cookie file exists
    def is_cookie_file(self):
        return os.path.exists(self.cookies_file_path)

    # Load cookies from file
    def load_cookies(self):
        # Load cookies from the file
        cookies_file = open(self.cookies_file_path, 'rb')
        cookies = pickle.load(cookies_file)

        for cookie in cookies:
            self.driver.add_cookie(cookie)

        cookies_file.close()

        self.go_to_page(self.url)

    # Save cookies to file
    def save_cookies(self):
        # Do not save cookies if there is no cookies_file name
        if not hasattr(self, 'cookies_file_path'):
            return

        # Create folder for cookies if there is no folder in the project
        if not os.path.exists(self.cookies_folder):
            os.mkdir(self.cookies_folder)

        # Open or create cookies file
        cookies_file = open(self.cookies_file_path, 'wb')

        # Get current cookies from the driver
        cookies = self.driver.get_cookies()

        # Save cookies in the cookie file as a byte stream
        pickle.dump(cookies, cookies_file)

        cookies_file.close()

    # Check if user is logged in based on a html element that is visible only for logged in users
    def is_logged_in(self, wait_element_time=None):
        if wait_element_time is None:
            wait_element_time = self.wait_element_time

        return self.find_element(self.is_logged_in_selector, False, wait_element_time)

    # Wait random amount of seconds before taking some action so the server won't be able to tell if you are a bot
    def wait_random_time(self):
        random_sleep_seconds = round(random.uniform(0.20, 1.20), 2)
        time.sleep(random_sleep_seconds)

    # Goes to a given page and waits random time before that to prevent detection as a bot
    def go_to_page(self, page):
        # Wait random time before refreshing the page to prevent the detection as a bot
        self.wait_random_time()

        # Refresh the site url with the loaded cookies so the user will be logged in
        self.driver.get(page)

    def find_element(self, selector, exit_on_missing_element=True, wait_element_time=None):
        return self._find_element(selector=selector, exit_on_missing_element=exit_on_missing_element,
                                  wait_element_time=wait_element_time)

    def find_element_by_xpath(self, xpath, exit_on_missing_element=True, wait_element_time=None):
        return self._find_element(xpath=xpath, exit_on_missing_element=exit_on_missing_element,
                                  wait_element_time=wait_element_time)

    def _find_element(self, selector=None, xpath=None, exit_on_missing_element=True, wait_element_time=None):
        if wait_element_time is None:
            wait_element_time = self.wait_element_time

        # Intialize the condition to wait
        if xpath:
            wait_until = EC.element_to_be_clickable((By.XPATH, xpath))
        elif selector:
            wait_until = EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        # Wait for element to load
        try:
            element = WebDriverWait(self.driver, wait_element_time).until(wait_until)
        except Exception as e:
            if not exit_on_missing_element:
                return False
            raise e
        return element

    def element_click(self, selector, delay=True, exit_on_missing_element=True, wait_element_time=None):
        return self._element_click(selector=selector, delay=delay, exit_on_missing_element=exit_on_missing_element, wait_element_time=wait_element_time)

    def element_click_by_xpath(self, xpath, delay=True, exit_on_missing_element=True, wait_element_time=None):
        return self._element_click(xpath=xpath, delay=delay, exit_on_missing_element=exit_on_missing_element, wait_element_time=wait_element_time)

    # Wait random time before clicking on the element
    def _element_click(self, selector=None, xpath=None, delay=True, exit_on_missing_element=True, wait_element_time=None):
        if not selector and not xpath:
            return
        if delay:
            self.wait_random_time()
        if selector:
            element = self.find_element(selector, exit_on_missing_element=exit_on_missing_element, wait_element_time=wait_element_time)
        elif xpath:
            element = self.find_element_by_xpath(xpath, exit_on_missing_element=exit_on_missing_element, wait_element_time=wait_element_time)
        if not element:
            return None
        try:
            element.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", element)
        return element

    # Wait random time before sending the keys to the element
    def _element_send_keys(self, text, xpath=None, selector=None, delay=True, exit_on_missing_element=True, wait_element_time=wait_element_time):
        if not xpath and not selector:
            raise Exception("no selector or xpath passed")
        if delay:
            self.wait_random_time()
        if xpath:
            element = self.find_element_by_xpath(selector, exit_on_missing_element=exit_on_missing_element, wait_element_time=wait_element_time)
        elif selector:
            element = self.find_element(selector,exit_on_missing_element=exit_on_missing_element, wait_element_time=wait_element_time)
        if not element:
            return None
        try:
            element.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", element)
        element.send_keys(text)
        return element

    def element_send_keys(self, selector, text, delay=True, exit_on_missing_element=True, wait_element_time=wait_element_time):
        return self._element_send_keys(text, selector=selector, delay=delay, exit_on_missing_element=exit_on_missing_element, wait_element_time=wait_element_time)

    def element_send_keys_by_xpath(self, xpath, text, delay=True, exit_on_missing_element=True, wait_element_time=wait_element_time):
        return self._element_send_keys(text, xpath=xpath, delay=delay, exit_on_missing_element=exit_on_missing_element, wait_element_time=wait_element_time)

    def input_file_add_files(self, selector, files, wait_element_time=30):
        # Intialize the condition to wait
        wait_until = EC.presence_of_element_located((By.CSS_SELECTOR, selector))

        try:
            # Wait for input_file to load
            input_file = WebDriverWait(self.driver, wait_element_time).until(wait_until)
        except:
            raise Exception('Timed out waiting for the input_file with selector "' + selector + '" to load')

        self.wait_random_time()

        try:
            input_file.send_keys(files)
        except InvalidArgumentException:
            logger.error('Exiting from the program! Please check if these file paths are correct:\n' + files)
            sys.exit()

    # Wait random time before clearing the element
    def element_clear(self, selector, delay=True):
        if delay:
            self.wait_random_time()

        element = self.find_element(selector)

        element.clear()

    def element_delete_text(self, selector, delay=True):
        if delay:
            self.wait_random_time()

        element = self.find_element(selector)

        # Select all of the text in the input
        element.send_keys(Keys.LEFT_SHIFT + Keys.HOME)
        # Remove the selected text with backspace
        element.send_keys(Keys.BACK_SPACE)

    def element_wait_to_be_invisible(self, selector):
        wait_until = EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))

        try:
            WebDriverWait(self.driver, self.wait_element_time).until(wait_until)
        except:
            logger.error('waiting the element with selector "' + selector + '" to be invisible')

    def _scroll_to_element(self, selector=None, xpath=None):
        if not selector and not xpath:
            return
        if xpath:
            self.find_element_by_xpath(xpath)
        elif selector:
            element = self.find_element(selector)

        self.driver.execute_script('arguments[0].scrollIntoView(true);', element)

    def scroll_to_element(self, selector):
        return self._scroll_to_element(selector=selector)

    def scroll_to_element_by_xpath(self, xpath):
        return self._scroll_to_element(xpath=xpath)
