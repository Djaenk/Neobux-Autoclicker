from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import TimeoutException

from PIL import Image

import os
import getpass
import base64
from io import BytesIO

class Neobux:

    _AD_HEADER = (By.XPATH, "/html/body/table/tbody/tr[1]/td/table/tbody/tr/td/table/tbody/tr/td[1]/table/tbody/tr")
    _LOGIN_ROWS_XPATH = "./table/tbody/tr[1]/td/table/tbody/tr"
    _DASHBOARD = (By.XPATH, "/html/body/div[2]/div/table")

    def __init__(self):
        self.driver_type = None
        if not self.driver_type:
            try:
                from selenium.webdriver.firefox.options import Options
                options = Options()
#                options.headless = True
                self.driver = webdriver.Firefox(options = options, service_log_path = os.path.devnull)
                self.driver_type = "geckodriver"
            except WebDriverException:
                self.driver_type = None
                del options
                del self.driver
        if not self.driver_type:
            try:
                from selenium.webdriver.chrome.options import Options
                options = Options()
                options.headless = True
                self.driver = webdriver.Chrome(options = options, service_log_path = os.path.devnull)
                self.driver_type = "chromedriver"
            except WebDriverException:
                self.driver_type = None
                del options
                del self.driver
        if not self.driver_type:
            self.driver = webdriver.PhantomJS(service_log_path = os.path.devnull)
            self.driver_type = "ghostdriver"
        self.actions = ActionChains(self.driver)
        self.load = WebDriverWait(self.driver, 5, poll_frequency = 0.2)
        self.wait = WebDriverWait(self.driver, 60)
        self.username = None
        self.password = None
        self.secondary_password = None
        self.captcha_image = None
        self.captcha = None
        self.stale_ad_count = 0
        self.fresh_ad_count = 0
        self.adprize_count = 0

    def action_click(self, element):
        self.driver.execute_script("return arguments[0].scrollIntoView();", element)
        self.actions.move_to_element(element).perform()
        element.click()

    def launch(self):
        self.driver.get("https://www.neobux.com/")
        login = self.load.until(expected_conditions.element_to_be_clickable((By.LINK_TEXT, "Login")))
        login.click()
        self.load.until(expected_conditions.element_to_be_clickable((By.ID, "loginform")))

    def prompt_login(self):
            self.username = input("Username: ")
            self.password = getpass.getpass()
            self.secondary_password = getpass.getpass("Secondary Password: ")
            self.captcha = input("Verification Code: ")

    def get_captcha(self):
        login_form = self.driver.find_element_by_id("loginform")
        input_rows = login_form.find_elements_by_xpath(Neobux._LOGIN_ROWS_XPATH)
        if len(input_rows) == 4:
            captcha = input_rows[3].find_element_by_xpath("./td/table/tbody/tr/td[@align='right']/img")
            captcha_input = input_rows[3].find_element_by_xpath("./td/table/tbody/tr/td[@align='left']/input")
            src = captcha.get_attribute("src")
            base64_data = src.replace("data:image/png;base64,", "")
            data = base64.b64decode(base64_data)
            self.captcha_image = Image.open(BytesIO(data))
            self.captcha_image = Image.composite(image, Image.new("RGB", image.size, "white"), image)
            return True
        else:
            return False

    def log_in(self):
        login_form = self.driver.find_element_by_id("loginform")
        input_rows = login_form.find_elements_by_xpath(Neobux._LOGIN_ROWS_XPATH)
        username_input = input_rows[0].find_element_by_xpath("./td/input[@placeholder='Username']")
        password_input = input_rows[1].find_element_by_xpath("./td/input[@placeholder='Password']")
        secondary_password_input = input_rows[2].find_element_by_xpath("./td/input[@placeholder='Secondary Password']")
        if get_captcha():
            self.captcha_image.show()
            captcha_input.send_keys(solution)
        send = login_form.find_element_by_link_text("send")
        username_input.click()
        username_input.send_keys(self.username)
        password_input.click()
        password_input.send_keys(self.password)
        secondary_password_input.click()
        secondary_password_input.send_keys(self.secondary_password)
        send.click()
        try:
            self.load.until(expected_conditions.element_to_be_clickable(Neobux._DASHBOARD))
            return True
        except TimeoutException:
            return False

    def view_ads(self):
        view = self.driver.find_element_by_link_text("View Advertisements")
        view.click()
        self.load.until(expected_conditions.element_to_be_clickable((By.CLASS_NAME, "cell")))

    def click_ads(self):
        ads = self.driver.find_elements_by_class_name("cell")
        for ad in ads:
            print("stale ads: %i, clicked ads: %i" % (self.stale_ad_count, self.fresh_ad_count), end= "\r", flush=True)
            self.action_click(ad)
            self.load.until(lambda d : "Click the red dot" in ad.text)
            dot = ad.find_element_by_tag_name("img")
            self.action_click(dot)
            self.driver.switch_to.window(self.driver.window_handles[1])
            header = self.load.until(expected_conditions.element_to_be_clickable(Neobux._AD_HEADER))
            if "You already saw this advertisement" in header.text:
                self.stale_ad_count += 1
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                adprize = self.driver.find_element_by_id("adprize").find_element_by_xpath("../div/div[2]")
                self.adprize_count = int(adprize.text)
                self.actions = ActionChains(self.driver)
                continue
            self.wait.until(expected_conditions.text_to_be_present_in_element(Neobux._AD_HEADER, "Advertisement validated!"))
            close = header.find_element_by_link_text("Close")
            close.click()
            self.fresh_ad_count += 1
            self.driver.switch_to.window(self.driver.window_handles[0])
            self.actions.reset_actions()
            self.actions = ActionChains(self.driver)
        print("")

    def click_adprize(self):
        adprize = self.driver.find_element_by_id("adprize").find_element_by_xpath("../div/div[2]")
        self.adprize_count = int(adprize.text)
        if self.adprize_count > 0:
            adprize.click()
            self.driver.switch_to.window(self.driver.window_handles[1])
            while True:
                print("Adprize remaining: %i" % (self.adprize_count), end= "\r", flush=True)
                try:
                    header = self.load.until(expected_conditions.element_to_be_clickable(Neobux._AD_HEADER))
                    self.wait.until(expected_conditions.text_to_be_present_in_element(Neobux._AD_HEADER, "Advertisement validated!"))
                    self.load.until(lambda d : header.find_element_by_id("rmnDv").text)
                    self.adprize_count = int(header.find_element_by_id("rmnDv").text)
                    next = header.find_element_by_link_text("Next")
                    next.click()
                except TimeoutException:
                    close = header.find_element_by_link_text("Close")
                    close.click()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    break

    def __del__(self):
        self.driver.quit()

if __name__ == "__main__":
    clicker = Neobux()
    clicker.launch()
    clicker.prompt_login()
    clicker.log_in()
    clicker.view_ads()
    clicker.click_ads()
    clicker.click_adprize()
