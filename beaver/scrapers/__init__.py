from selenium import webdriver
import logging
import sys

class Scraper:
    def __init__(self, driver, headless=True, silent=True):
        if driver == 'firefox':
            self.init_firefox_driver(headless)
        elif driver == 'chrome':
            self.init_chrome_driver(headless)
        if not silent:
            logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    def init_chrome_driver(self, headless):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        self.driver = webdriver.Firefox(chrome_options=options)

    def init_firefox_driver(self, headless):
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument('--headless')
        self.driver = webdriver.Firefox(firefox_options=options)
