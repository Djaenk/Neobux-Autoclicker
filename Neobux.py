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
from base64 import b64decode
from io import BytesIO

class Neobux:
    """Neobux advertisement autoclicker object based on python selenium webdriver"""

    AD_HEADER = (By.XPATH, "/html/body/table/tbody/tr[1]/td/table/tbody/tr/td/table/tbody/tr/td[1]/table/tbody/tr")
    LOGIN_ROWS_XPATH = "./table/tbody/tr[1]/td/table/tbody/tr"
    DASHBOARD_XPATH = "/html/body/div[2]/div/table"
    ERROR_MESSAGE_XPATH = "//*[text()='Error:']"
    FAVICON_BASE64 = ("iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAatJREFU"
                      "OI19k09rE0Echt+1rVA9bNKiByHNh/Hg9xA8SY3uqdX1EL142G4gtVoQD16lBD0ISv6AHoL0UBAD"
                      "Ro2IHmKy+OeSUpBOHg/uJpvs6MALAzPPs/ub+Y0UD2C12+0OAVf/GAxYax21IoK5PcCZSqUyloTn"
                      "eQbIZeA+heBLgF6I8vuy4W4sAVYSOEmpVJqR0KcYfP0LqynUiCUbuOp0OsM0nCT+k0X6nEu+rGYq"
                      "z8UBB5GAXBiGxibZDXZH1Z/VwwzcEP4733B9WkbeKrkotCP0ygLfyx7krOSy0B2hckpigReTieM4"
                      "v4BTS87Sj/Xu+mkVJB1LWpD0XdIb6eaFa4e3ardXnA3nd8KdmLutVcCxNsHxps4uhNKyfVlAMQiC"
                      "af3pErY30TNQDbz9saHXzM3DhRk4ySWhagw/jfMErr42UwmwZoUlbpSujMLPjLSXEsQSb39seFhw"
                      "Va/XIxvs+74BTvLt7fJWD5OR7EGrTyTA9X3fWODJVTHo5MNPKUkNHnzEcL84aaSJZB5OS7Z6GD2O"
                      "4UfnM43kttvtwX+fc/Qh/3LAkJ3iZM8fgE6YK+IA+xEAAAAASUVORK5CYII=")

    def __init__(self):
        """Initializes the webdriver, first attempting Firefox then Chrome
        initialization before defaulting to PhantomJS. After initialization
        of webdriver, launches Neobux site."""
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
        self.load = WebDriverWait(self.driver, 5, poll_frequency = 0.1)
        self.wait = WebDriverWait(self.driver, 60)
        self.username = None
        self.password = None
        self.secondary_password = None
        self.captcha_image = None
        self.captcha_key = None
        self.ad_count = 0
        self.stale_ad_count = 0
        self.fresh_ad_count = 0
        self.adprize_count = 0
        self.launch()

    def action_click(self, element):
        """Helper function to emulate hovering over an element before clicking
        it. This is necessary when clicking on an advertisement to be allowed to
        view it."""
        self.driver.execute_script("return arguments[0].scrollIntoView();", element)
        self.actions.move_to_element(element).perform()
        element.click()

    def launch(self):
        """Prepares the webdriver for Neobux operation by getting the login screen.
        To be used after intializing a selenium webdriver."""
        self.driver.get("https://www.neobux.com/")
        login = self.load.until(expected_conditions.element_to_be_clickable((By.LINK_TEXT, "Login")))
        login.click()
        self.load.until(expected_conditions.element_to_be_clickable((By.ID, "loginform")))

    def prompt_login(self):
        """Prompts the user for login credentials from the command line"""
        self.username = input("Username: ")
        self.password = getpass.getpass()
        self.secondary_password = getpass.getpass("Secondary Password: ")

    def prompt_captcha(self):
        """Prompts the user for the captcha key from the command line"""
        self.captcha_key = input("Verification Code: ")

    def get_captcha(self):
        """Returns True and sets captcha image of the clicker if there exists a
        captcha. Otherwise, returns False
        Only call this after launching the clicker and before successful login"""
        login_form = self.driver.find_element_by_id("loginform")
        input_rows = login_form.find_elements_by_xpath(Neobux.LOGIN_ROWS_XPATH)
        if len(input_rows) == 4:
            captcha = input_rows[3].find_element_by_xpath("./td/table/tbody/tr/td[@align='right']/img")
            captcha_input = input_rows[3].find_element_by_xpath("./td/table/tbody/tr/td[@align='left']/input")
            src = captcha.get_attribute("src")
            base64_data = src.replace("data:image/png;base64,", "")
            self.captcha_image = Image.open(BytesIO(b64decode(base64_data)))
            #self.captcha_image = Image.composite(self.captcha_image, Image.new("RGB", self.captcha_image.size, "white"), self.captcha_image)
            return True
        else:
            return False

    def log_in(self):
        """Attempts to log into Neobux with the set credentials.
        If login is successful, returns True. Otherwise, sets the clicker
        login error message and returns False."""
        login_form = self.driver.find_element_by_id("loginform")
        input_rows = login_form.find_elements_by_xpath(Neobux.LOGIN_ROWS_XPATH)
        username_input = input_rows[0].find_element_by_xpath("./td/input[@placeholder='Username']")
        password_input = input_rows[1].find_element_by_xpath("./td/input[@placeholder='Password']")
        secondary_password_input = input_rows[2].find_element_by_xpath("./td/input[@placeholder='Secondary Password']")
        if self.get_captcha():
            captcha_input = input_rows[3].find_element_by_xpath("./td/table/tbody/tr/td[@align='left']/input")
            captcha_input.click()
            captcha_input.send_keys(self.captcha_key)
        username_input.click()
        username_input.send_keys(self.username)
        password_input.click()
        password_input.send_keys(self.password)
        secondary_password_input.click()
        secondary_password_input.send_keys(self.secondary_password)
        send = login_form.find_element_by_link_text("send")
        send.click()
        try:
            self.load.until(lambda driver : driver.find_elements_by_xpath(Neobux.DASHBOARD_XPATH) or driver.find_elements_by_xpath(Neobux.ERROR_MESSAGE_XPATH))
            if self.driver.find_elements_by_xpath(Neobux.DASHBOARD_XPATH):
                return True
            else:
                self.login_error = driver.find_element_by_xpath(Neobux.ERROR_MESSAGE_XPATH).find_element_by_xpath("..").text
                self.launch()
                return False
        except TimeoutException:
            if username_input.value_of_css_property("background-color") is "rgb(255, 221, 204)":
                self.login_error = "Error: Invalid Username"
            elif password_input.value_of_css_property("background-color") is "rgb(255, 221, 204)":
                self.login_error = "Error: Invalid Password"
            elif secondary_password_input.value_of_css_property("background-color") is "rgb(255, 221, 204)":
                self.login_error = "Error: Invalid Secondary Password"
            else:
                self.login_error = "Error: Possibly unstable, slow, or blocked connection"
            return False

    def view_ads(self):
        """Navigates to the page of advertisements by clicking the "View
        Advertisements" link in the navigation menu. Counts and stores the
        number of advertisements available after navigating."""
        view = self.driver.find_element_by_link_text("View Advertisements")
        view.click()
        self.load.until(expected_conditions.element_to_be_clickable((By.CLASS_NAME, "cell")))
        try:
            self.driver.find_element_by_link_text("disable").click()
        except:
            pass
        self.ad_count = len(self.driver.find_elements_by_class_name("cell"))
        print("Availabled advertisements: %i" % (self.ad_count))

    def click_ads(self):
        """Identifies the advertisements available to click and clicks through
        each. If the ad has already been clicked, then stale ad count is
        incremented and immediately moves on to the next ad. If not, then fresh
        ad count is incremented and waits for advertisement validation before
        continuing.
        Only call this function when the webdriver is on the view
        advertisements page."""
        ads = self.driver.find_elements_by_class_name("cell")
        for ad in ads:
            print("stale ads: %i, clicked ads: %i" % (self.stale_ad_count, self.fresh_ad_count), end= "\r", flush=True)
            self.action_click(ad)
            self.load.until(lambda d : "Click the red dot" in ad.text)
            dot = ad.find_element_by_tag_name("img")
            self.action_click(dot)
            self.driver.switch_to.window(self.driver.window_handles[1])
            header = self.load.until(expected_conditions.element_to_be_clickable(Neobux.AD_HEADER))
            if "You already saw this advertisement" in header.text:
                self.stale_ad_count += 1
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                adprize = self.driver.find_element_by_id("adprize").find_element_by_xpath("../div/div[2]")
                self.adprize_count = int(adprize.text)
                self.actions = ActionChains(self.driver)
            else:
                self.wait.until(expected_conditions.text_to_be_present_in_element(Neobux.AD_HEADER, "Advertisement validated!"))
                close = header.find_element_by_link_text("Close")
                close.click()
                self.fresh_ad_count += 1
                self.driver.switch_to.window(self.driver.window_handles[0])
                self.actions.reset_actions()
                self.actions = ActionChains(self.driver)
        print("")

    def get_adprize_count(self):
        """Sets the adprize count to number of remaining adprize.
        Only call this function when the webdriver is on the view
        advertisements page."""
        adprize = self.driver.find_element_by_id("adprize").find_element_by_xpath("../div/div[2]")
        self.adprize_count = int(adprize.text)
        print("Adprize: %i" % (self.adprize_count))

    def click_adprize(self):
        """Clicks through the adprize if the adprize count is greater than zero.
        Updates the adprize count on each successful advertisement validation.
        Only call this function when the webdriver is on the view
        advertisements page."""
        adprize = self.driver.find_element_by_id("adprize").find_element_by_xpath("../div/div[2]")
        self.adprize_count = int(adprize.text)
        print("Adprize: %i" % (self.adprize_count))
        if self.adprize_count > 0:
            adprize.click()
            self.driver.switch_to.window(self.driver.window_handles[1])
            while True:
                print("Adprize remaining: %i" % (self.adprize_count), end= "\r", flush=True)
                try:
                    header = self.load.until(expected_conditions.element_to_be_clickable(Neobux.AD_HEADER))
                    self.wait.until(expected_conditions.text_to_be_present_in_element(Neobux.AD_HEADER, "Advertisement validated!"))
                    self.load.until(lambda d : header.find_element_by_id("rmnDv").text)
                    self.adprize_count = int(header.find_element_by_id("rmnDv").text)
                    next = header.find_element_by_link_text("Next")
                    next.click()
                except TimeoutException:
                    self.adprize_count = 0
                    close = header.find_element_by_link_text("Close")
                    close.click()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    break

    def __del__(self):
        """Ensure webdriver cleanup upon clicker deletion"""
        self.driver.quit()

if __name__ == "__main__":
    clicker = Neobux()
    clicker.prompt_login()
    if clicker.get_captcha():
        clicker.captcha_image.show()
        clicker.prompt_captcha()
    clicker.log_in()
    clicker.view_ads()
    clicker.click_ads()
    clicker.click_adprize()