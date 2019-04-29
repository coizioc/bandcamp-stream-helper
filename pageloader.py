from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options
import os

from threading import Thread, Condition


class HTMLScraperThread(Thread):
    def __init__(self, url, css_selector=None):
        Thread.__init__(self)
        self.url = url
        self.css_selector = css_selector
        self.cv = Condition()
        self.html_str = None

    def run(self):
        if os.path.isfile('geckodriver.exe'):
            options = webdriver.firefox.options.Options()
            options.add_argument("--headless")
            options.add_argument("--window-size=1024x1400")
            options.add_argument("--log-level=3")
            firefox_driver = os.path.join(os.getcwd(), "geckodriver")
            driver = webdriver.Firefox(firefox_options=options, executable_path=firefox_driver)
        else:
            options = webdriver.chrome.options.Options()
            options.add_argument("--headless")
            options.add_argument("--window-size=1024x1400")
            options.add_argument("--log-level=3")
            chrome_driver = os.path.join(os.getcwd(), "chromedriver")
            driver = webdriver.Chrome(chrome_options=options, executable_path=chrome_driver)

        driver.get(self.url)

        if self.css_selector:
            div_elem = driver.find_element_by_css_selector(self.css_selector)
            html_str = div_elem.get_attribute('innerHTML')
        else:
            html_str = driver.page_source

        driver.close()
        self.html_str = html_str
        with self.cv:
            self.cv.notify()
