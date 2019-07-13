import os
import traceback

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException

from multiprocessing.connection import PipeConnection
import threading
import queue

import getpass
from base64 import b64decode
from io import BytesIO
from PIL import Image

from enum import Enum

def _discern_page(driver):
    """Helper function to determine the current page of the webdriver"""
    url = driver.current_url
    if url is "about:blank":
        return NeobuxPage.NONE
    elif url is "https://www.neobux.com/":
        return NeobuxPage.HOME
    elif "https://www.neobux.com/m/l/" in url:
        return NeobuxPage.LOGIN
    elif "https://www.neobux.com/m/ga/" in url:
        return NeobuxPage.VERIFICATION
    elif "https://www.neobux.com/m/tta/" in url:
        return NeobuxPage.LOGIN_LOG
    elif "https://www.neobux.com/c/" in url:
        return NeobuxPage.DASHBOARD
    elif "https://www.neobux.com/c/rs/" in url:
        return NeobuxPage.STATISTICS
    elif "https://www.neobux.com/m/v/" in url:
        return NeobuxPage.VIEW
    elif "https://www.neobux.com/v/" in url:
        return NeobuxPage.AD
    elif "https://www.neobux.com/m/l0/" in url:
        return NeobuxPage.LOGOUT
    else:
        return None

def _action_click(driver, actions, element):
    """Helper function to emulate hovering then clicking an element
        
    This is necessary when clicking on an advertisement to be allowed to
    view it.
    """
    driver.execute_script("return arguments[0].scrollIntoView();", element)
    actions.move_to_element(element).perform()
    element.click()

class Neobux:
    """Neobux advertisement autoclicker object based on python selenium webdriver"""

    AD_HEADER = (By.XPATH, "/html/body/table/tbody/tr[1]/td/table/tbody/tr/td/table/tbody/tr/td[1]/table/tbody/tr")
    LOGIN_ROWS = (By.XPATH, "./table/tbody/tr[1]/td/table/tbody/tr") #relative to the login form
    ERROR_MESSAGE = (By.XPATH, "//*[text()='Error:']")
    SUMMARY = (By.XPATH, "/html/body/div[2]/div/table/tbody/tr/td[3]/table/tbody/tr/td/div/table[1]/tbody/tr/td[1]/table")
    AD_LIST_BODY = (By.ID, "tl")
    FAVICON_BASE64 = ("iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAatJREFU"
                      "OI19k09rE0Echt+1rVA9bNKiByHNh/Hg9xA8SY3uqdX1EL142G4gtVoQD16lBD0ISv6AHoL0UBAD"
                      "Ro2IHmKy+OeSUpBOHg/uJpvs6MALAzPPs/ub+Y0UD2C12+0OAVf/GAxYax21IoK5PcCZSqUyloTn"
                      "eQbIZeA+heBLgF6I8vuy4W4sAVYSOEmpVJqR0KcYfP0LqynUiCUbuOp0OsM0nCT+k0X6nEu+rGYq"
                      "z8UBB5GAXBiGxibZDXZH1Z/VwwzcEP4733B9WkbeKrkotCP0ygLfyx7krOSy0B2hckpigReTieM4"
                      "v4BTS87Sj/Xu+mkVJB1LWpD0XdIb6eaFa4e3ardXnA3nd8KdmLutVcCxNsHxps4uhNKyfVlAMQiC"
                      "af3pErY30TNQDbz9saHXzM3DhRk4ySWhagw/jfMErr42UwmwZoUlbpSujMLPjLSXEsQSb39seFhw"
                      "Va/XIxvs+74BTvLt7fJWD5OR7EGrTyTA9X3fWODJVTHo5MNPKUkNHnzEcL84aaSJZB5OS7Z6GD2O"
                      "4UfnM43kttvtwX+fc/Qh/3LAkJ3iZM8fgE6YK+IA+xEAAAAASUVORK5CYII=")

    def __init__(self, driver_type = None, threading = False, connection = None):
        """Creates a selenium webdriver
        
        Initializes the webdriver, using a webdriver of the type specified. If
        no driver type is specified, attempts to start a Firefox session, then
        a Chrome session if Firefox fails, then defaults to PhantomJS if Chrome
        fails. After initialization of webdriver, launches Neobux site.

        The threading argument can be passed a truthy value to make the
        instance run its methods in another thread. However, to protect
        the webdriver, some methods manipulating the driver will be placed into
        a queue to be threaded one at a time.

        A connection can be provided to allow the Neobux instance to receive
        commands and send return values through a pipe after entering the
        mainloop. Functions can be invoked by sending specific command strings
        followed by the argument functions.
        """
        #multithreading/multiprocessing setup
        self._blocking_threads = queue.Queue()
        self._current_blocking_thread = None
        self._nonblocking_threads = []
        self.set_threading(threading)
        self.set_connection(connection, True)

        #webdriver setup
        if driver_type is None or "Firefox" or "geckodriver":
            try:
                from selenium.webdriver.firefox.options import Options
                options = Options()
                options.headless = True
                self.driver = webdriver.Firefox(options = options, service_log_path = os.path.devnull)
                self.driver_type = "geckodriver"
            except WebDriverException:
                del options
        elif driver_type is None or "Chrome" or "chromedriver":
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
        elif driver_type is None or "PhantomJS" or "ghostdriver":
            self.driver = webdriver.PhantomJS(service_log_path = os.path.devnull)
            self.driver_type = "ghostdriver"
        else:
            raise ValueError("Invalid driver type, must be 'Firefox', 'Chrome', or 'PhantomJS'")
        self.actions = ActionChains(self.driver)
        self.load = WebDriverWait(self.driver, 5, poll_frequency = 0.1)
        self.wait = WebDriverWait(self.driver, 90)

        #clicker setup
        self.page = NeobuxPage.NONE
        self.credentials = {
            "username" : "",
            "password" : "",
            "secondary" : "",
            "captcha" : ""
        }
        self.captcha_image = None
        self.authentication_number = ""
        self.login_error = None
        self.click_count = 0
        self.adprize_count = 0
        self.summary = {
            "membership" : "",
            "member since" : "",
            "seen advertisements" : 0,
            "main balance" : 0,
            "rental balance" : 0,
            "points" : 0
        }
        self.statistics = {
            "unique" : {"Clicks" : 0, "Average" : 0},
            "fixed" : {"Clicks" : 0, "Average" : 0},
            "micro" : {"Clicks" : 0, "Average" : 0},
            "mini" : {"Clicks" : 0, "Average" : 0},
            "standard" : {"Clicks" : 0, "Average" : 0},
            "extended" : {"Clicks" : 0, "Average" : 0}
        }
        self.ad_counts = {
            "total" : 0,
            "stale" : 0,
            "unique" : 0,
            "fixed" : 0,
            "micro" : 0,
            "mini" : 0,
            "standard" : 0,
            "extended" : 0
        }

    def set_threading(self, threading):
        """Enables/Disables threading for instance method execution
        
        Accepts truthy and falsy values to enable or disable instance
        threading.
        
        If threading is set to false with methods still queued for
        execution, the remaining methods will all execute and block the
        instance until they have completed.
        """
        if threading:
            self._threading = True
            self._assign_threads()
        else:
            self._threading = False
            self._blocking_threads.join()

    def _assign_threads(self):
        #check if another blocking thread is alive
        if self._current_blocking_thread is None:
            blocked = False
        elif not self._current_blocking_thread.is_alive():
            self._blocking_threads.task_done()
            blocked = False
        else:
            blocked = True
        if not blocked:
            try:
                method = self._blocking_threads.get_nowait()
                self._current_blocking_thread = threading.Thread(target = method[0], args = method[1:])
                self._current_blocking_thread.start()
            except queue.Empty:
                self._current_blocking_thread = None
        for method in self._nonblocking_threads:
            threading.Thread(target = method[0], args = method[1:]).start()
        self._nonblocking_threads = []
        if self._threading or not self._blocking_threads.empty():
            threading.Timer(0.1, self._assign_threads).start()
            #reschedule self to run after 100 milliseconds while threading is enabled

    def set_connection(self, connection = None, targeted = False):
        """Sets the connection of the clicker instance to the object passed

        If an object that is not a connection is passwed, raises TypeError.
        To remove the instance's reference to its current connection, pass
        None or no argument.

        :raises: TypeError
        """
        if self._threading and not targeted:
            self._blocking_threads.put((self.set_connection, connection, True))
            return
        if isinstance(connection, PipeConnection):
            self._connection = connection
        elif not connection:
            self._connection = None
        else:
            raise TypeError("argument is not a multiprocessing.connection.Connection object")

    def mainloop(self, timeout = 0.1):
        """Runs an infinite loop, enters operation via the connection

        The instance enters an infinite loop. From within the loop, operations
        are performed by sending instructions in the form of tuples.

        To set or retrieve a data attribute, the first element of the tuple
        must be a string containing the name of the desired attribute. If there
        exists a second element, then it is assigned to the specified data
        attribute. If not, then the value of the data attribute is sent back
        through the pipe.

        To invoke an instance method, the first element of the tuple must be
        a string containing the name of the method. All proceeding elements, if
        any, will be passed to the method as arguments. If the invoked method
        returns a value, that value is sent back through the pipe.

        Operations pertaining to the mainloop can be performed by sending
        tuples wherein the second elements are any of the following:
        * "timeout" - sets or retrieves the time in seconds of how long the
            mainloop waits for an instruction on each interation
        * "exit_loop" - breaks out of the infinite loop, allowing mainloop to
            return

        If an invalid instruction is received by the loop, it is discarded and
        a string containing an error message is sent back through the pipe.

        This mode of operation is useful if the Neobux clicker object is to be
        run in a separate thread/process for asynchronous usage. However,
        calling the mainloop and entering this mode of operation is not
        necessary to use this class; simply calling the class methods is
        sufficient for many use cases.
        """
        if not self._connection:
            raise AttributeError("mainloop cannot be run without an instance Connection object")
        while True:
            if self._connection.poll(timeout):
                instruction = self._connection.recv()
            else:
                continue
            if isinstance(instruction, tuple):
                if hasattr(self, instruction[0]):
                    if callable(instruction[0]):
                        function = getattr(self, instruction[0])
                        args = instruction[1:]
                        retval = function(*args)
                        if retval is not None:
                            self._connection.send(retval)
                    else:
                        variable = getattr(self, instruction[0])
                        try:
                            variable = instruction[1]
                        except IndexError:
                            self._connection.send(variable)
                elif instruction[0] == "timeout":
                    try:
                        timeout = instruction[1]
                    except IndexError:
                        self._connection.send(timeout)
                elif instruction[0] == "exit_loop":
                    break
                else:
                    print(instruction[0])
                    raise ValueError("Invalid instruction: No such attribute")
            else:
                raise TypeError("Invalid instruction: not of class tuple")
            instruction = None

    def launch(self, targeted = False):
        """Prepares webdriver for Neobux operation by getting the login screen"""
        if self._threading and not targeted:
            self._blocking_threads.put((self.launch, True))
            return
        self.driver.get("https://www.neobux.com/")
        self.page = NeobuxPage.HOME
        login = self.load.until(expected_conditions.element_to_be_clickable((By.LINK_TEXT, "Login")))
        login.click()
        self.load.until(expected_conditions.element_to_be_clickable((By.ID, "loginform")))
        self.page = NeobuxPage.LOGIN
        self.set_captcha()

    def prompt_login(self, targeted = False):
        """Prompts the user for login credentials from the command line"""
        #if self._threading and not targeted:
        #    self._nonblocking_threads.append((self.prompt_login, True))
        #    return
        self.credentials["username"] = input("Username: ")
        self.credentials["password"] = getpass.getpass()
        self.credentials["secondary"] = getpass.getpass("Secondary Password: ")

    def prompt_captcha(self, targeted = False):
        """Prompts the user for the captcha key from the command line"""
        #if self._threading and not targeted:
        #    self._nonblocking_threads.append((self.prompt_captcha, True))
        #    return
        self.credentials["captcha"] = input("Verification Code: ")

    def prompt_authentication_number(self, targeted = False):
        """Prompts the user for the 2-Step Verification code from the command line"""
        #if self._threading and not targeted:
        #    self._nonblocking_threads.append((self.prompt_authenticaion_number, True))
        #    return
        self.authentication_number = input("Six digit authentication number: ")

    def set_captcha(self, targeted = False):
        """Sets instance captcha image
        
        If there exists a captcha at the login screen, self.captcha_image is
        set to an pillow Image object containing the captcha. If there isn't
        one, self.captcha_image is set to None. Only call this after launching
        the clicker and before successful login.
        """
        if self._threading and not targeted:
            self._blocking_threads.put((self.set_captcha, True))
            return
        login_form = self.driver.find_element_by_id("loginform")
        input_rows = login_form.find_elements(*Neobux.LOGIN_ROWS)
        if len(input_rows) == 4:
            captcha = input_rows[3].find_element_by_xpath("./td/table/tbody/tr/td[@align='right']/img")
            captcha_input = input_rows[3].find_element_by_xpath("./td/table/tbody/tr/td[@align='left']/input")
            src = captcha.get_attribute("src")
            base64_data = src.replace("data:image/png;base64,", "")
            self.captcha_image = Image.open(BytesIO(b64decode(base64_data)))
            self.captcha_image = Image.composite(self.captcha_image, Image.new("RGB", self.captcha_image.size, "white"), self.captcha_image)
            self.page = NeobuxPage.CAPTCHA
        else:
            self.captcha_image = None
            self.page = NeobuxPage.LOGIN

    def log_in(self, targeted = False):
        """Attempts to log in to Neobux using the instance username/password/key values"""
        if self._threading and not targeted:
            self._blocking_threads.put((self.log_in, True))
            return
        if self.page is not NeobuxPage.LOGIN:
            raise RuntimeError("Can only attempt to log in from the Neobux Login page")
        login_form = self.driver.find_element_by_id("loginform")
        input_rows = login_form.find_elements(*Neobux.LOGIN_ROWS)
        username_input = input_rows[0].find_element_by_xpath("./td/input[@placeholder='Username']")
        password_input = input_rows[1].find_element_by_xpath("./td/input[@placeholder='Password']")
        secondary_password_input = input_rows[2].find_element_by_xpath("./td/input[@placeholder='Secondary Password']")
        if self.captcha_image:
            captcha_input = input_rows[3].find_element_by_xpath("./td/table/tbody/tr/td[@align='left']/input")
            captcha_input.click()
            captcha_input.send_keys(self.credentials["captcha"])
        username_input.click()
        username_input.send_keys(self.credentials["username"])
        password_input.click()
        password_input.send_keys(self.credentials["password"])
        secondary_password_input.click()
        secondary_password_input.send_keys(self.credentials["secondary"])
        send = login_form.find_element_by_link_text("send")
        send.click()
        try:
            self.load.until(lambda driver : "https://www.neobux.com/m/l/" not in driver.current_url)
            self.login_error = None
            self.captcha_image = None
            self.page = _discern_page(self.driver)
        except TimeoutException:
            if self.driver.find_elements(*Neobux.ERROR_MESSAGE):
                self.login_error = self.driver.find_element(*Neobux.ERROR_MESSAGE).find_element_by_xpath("..").text
            elif username_input.value_of_css_property("background-color") is "rgb(255, 221, 204)":
                self.login_error = "Error: Invalid Username"
            elif password_input.value_of_css_property("background-color") is "rgb(255, 221, 204)":
                self.login_error = "Error: Invalid Password"
            elif secondary_password_input.value_of_css_property("background-color") is "rgb(255, 221, 204)":
                self.login_error = "Error: Invalid Secondary Password"

    def verify(self, targeted = False):
        """Attempts completion of 2-step verification using instance authorization number"""
        if self._threading and not targeted:
            self._blocking_threads.put((self.verify, True))
            return
        if self.page is not NeobuxPage.VERIFICATION:
            raise RuntimeError("Cannot input authorization code without 2-step verification prompt")
        verification_form = self.driver.find_element_by_id("form2stps")
        verification_form.find_element_by_tag_name("input").send_keys(self.authentication_number)
        verification_form.find_element_by_link_text("send").click()
        try:
            self.load.until(expected_conditions.staleness_of(verification_form))
            self.page = _discern_page(self.driver)
        except TimeoutException:
            self.login_error = verification_form.find_element_by_xpath("./*[style='color:#ac0000;font-weight:bold;'").text

    def view_dashboard(self, targeted = False):
        """Navigates to account dashboard and acquires account summary"""
        if self._threading and not targeted:
            self._blocking_threads.put((self.view_dashboard, True))
            return
        account = self.driver.find_element_by_link_text(self.username)
        account.click()
        self.load.until(expected_conditions.element_to_be_clickable(Neobux.SUMMARY))
        self.page = NeobuxPage.DASHBOARD
        summary = self.driver.find_element(*Neobux.SUMMARY)
        data = summary.text
        data = data.replace(" ", "")
        data = data.replace("=", "")
        data = data.replace("+", "")
        data = data.replace("$", "")
        data = data.split("\n")
        data = [entry.split(":")[-1] for entry in data]
        self.summary["membership"] = data[1]
        self.summary["since"] = data[2]
        self.summary["seen"] = int(data[4])
        self.summary["main_balance"] = int(data[7])
        self.summary["rental_balance"] = int(data[8])
        self.summary["points"] = int(data[10])
        
    def view_statistics(self, targeted = False):
        """Navigates to account statistics and acquires 10-day click statistics"""
        if self._threading and not targeted:
            self._blocking_threads.put((self.view_statistics, True))
            return
        statistics = self.driver.find_element_by_id("statBt")
        chart_bars = self.driver.find_elements_by_class_name("highcharts-color-0")
        self.load.until(expected_conditions.element_to_be_clickable((By.CLASS_NAME, "highcharts-container")))
        self.page = NeobuxPage.STATISTICS
        for bar in chart_bars:
            try:
                bar.click()
                tooltip = self.driver.find_element_by_css_selector(".highcharts-tooltip.highcharts-color-0")
                label = tooltip.text.split("Clicks: ")[0]
                data = tooltip.text.split("Clicks: ")[1]
                if label == "Fixed":
                    if tooltip.find_elements_by_class_name("highcharts-tooltip-box")[3].get_attribute("stroke") == "#E517F7":
                        label = "unique"
                    if tooltip.find_elements_by_class_name("highcharts-tooltip-box")[3].get_attribute("stroke") == "#FF9C00":
                        label = "fixed"
                clicks = int(data.split("Average: ")[0])
                average = int(data.split("Average: ")[1])
                self.statistics[label.lower()] = {"Clicks" : clicks, "Average" : average}
            except:
                pass

    def view_ads(self, targeted = False):
        """Navigates to the page of advertisements, sets instance ad count
        
        Webdriver clicks "View Advertisements" link in the navigation menu.
        After navigation, counts and stores the number of advertisements
        available.
        """
        if self._threading and not targeted:
            self._blocking_threads.put((self.view_ads, True))
            return
        view = self.driver.find_element_by_link_text("View Advertisements")
        view.click()
        self.load.until(expected_conditions.element_to_be_clickable((By.CLASS_NAME, "cell")))
        self.page = NeobuxPage.VIEW
        try:
            self.driver.find_element_by_link_text("disable").click()
        except:
            pass
        self.ad_counts["total"] = len(self.driver.find_elements_by_class_name("cell"))
        self.ad_counts["stale"] = len(self.driver.find_elements_by_class_name("c_ad0"))
        self.ad_counts["unique"] = len(self.driver.find_elements_by_class_name("c_adfu"))
        self.ad_counts["fixed"] = len(self.driver.find_elements_by_class_name("c_adf"))
        self.ad_counts["micro"] = len(self.driver.find_elements_by_class_name("c_ad5"))
        self.ad_counts["mini"] = len(self.driver.find_elements_by_class_name("c_ad30"))
        #self.standard_exposure = len(self.driver.find_elements_by_class_name(""))
        self.extended_exposure = len(self.driver.find_elements_by_class_name("c_ad15"))
        print("Advertisements:                      %i" % (self.ad_total))
        print("Already clicked:                     %i" % (self.stale_ads))
        print("Unique Fixed Advertisements:         %i" % (self.unique_fixed_ads))
        print("Fixed Advertisements:                %i" % (self.fixed_ads))
        #print("Micro Exposure:                      %i" % (self.micro_exposure))
        #print("Mini Exposure:                       %i" % (self.mini_exposure))
        #print("Standard Exposure:                   %i" % (self.standard_exposure))
        #print("Extended Exposure:                   %i" % (self.extended_exposure))

    def click_ads(self, targeted = False):
        """Clicks through the available advertisements

        Identifies the advertisements and iterates through each. On every
        iteration, an advertisement is clicked. If the advertisement has
        already been clicked, then stale ad count is incremented and
        iteration continues. If not, then fresh ad count is incremented and 
        the instance driver waits for advertisement validation before
        continuing.

        Only call this function when the webdriver is on the view
        advertisements page.
        """
        if self._threading and not targeted:
            self._blocking_threads.put((self.click_ads, True))
            return
        if self.page is not NeobuxPage.VIEW:
            raise RuntimeError("Cannot click ads without viewing advertisements")
        for index in range(self.ad_total):
            ad = self.driver.find_elements_by_class_name("cell")[index]
            if "c_ad0" in ad.get_attribute("class"):
                continue
            advertisements_url = self.driver.current_url
            self.actions.reset_actions()
            self.actions = ActionChains(self.driver)
            _action_click(self.driver, self.actions, ad)
            self.load.until(lambda d : "Click the red dot" in ad.text)
            dot = ad.find_element_by_tag_name("img")
            _action_click(self.driver, self.actions, dot)
            self.driver.switch_to.window(self.driver.window_handles[1])
            self.page = NeobuxPage.AD
            header = self.load.until(expected_conditions.element_to_be_clickable(Neobux.AD_HEADER))
            if "You already saw this advertisement" in header.text:
                self.driver.close()
            else:
                self.wait.until(expected_conditions.text_to_be_present_in_element(Neobux.AD_HEADER, "Advertisement validated!"))
                self.click_count += 1
                close = header.find_element_by_link_text("Close")
                close.click()
                print("clicked ads: %i" % (self.click_count), end= "\r", flush=True)
            self.driver.switch_to.window(self.driver.window_handles[0])
            self.page = NeobuxPage.VIEW
            self.load.until(lambda driver : driver.current_url is not advertisements_url)
            self.load.until(expected_conditions.element_to_be_clickable(Neobux.AD_LIST_BODY))
            try:
                adprize = self.driver.find_element_by_id("adprize").find_element_by_xpath("../div/div[2]")
                self.adprize_count = int(adprize.text)
            except NoSuchElementException:
                self.adprize_count = 0
        print("")

    def set_adprize_count(self, targeted = False):
        """Sets the instance adprize count to the number of adprize

        Only call this function when the webdriver is on the view
        advertisements page.
        """
        if self._threading and not targeted:
            self._blocking_threads.put((self.set_adprize_count, True))
            return
        if self.page is not NeobuxPage.VIEW:
            raise RuntimeError("Cannot acquire adprize count without viewing advertisements")
        adprize = self.driver.find_element_by_id("adprize").find_element_by_xpath("../div/div[2]")
        self.adprize_count = int(adprize.text)
        print("Adprize: %i" % (self.adprize_count))

    def click_adprize(self, targeted = False):
        """Clicks through the adprize if the adprize count
        
        Sets the instance adprize count to the number of adprize. If the
        instance adprize count is greater than zero, then the driver clicks
        through the adprize. Updates the instance adprize count on each
        advertisement validation.

        Only call this function when the webdriver is on the view
        advertisements page.
        """
        if self._threading and not targeted:
            self._blocking_threads.put((self.click_adprize, True))
            return
        if self.page is not NeobuxPage.VIEW:
            raise RuntimeError("Cannot click adprize without viewing advertisements")
        adprize = self.driver.find_element_by_id("adprize").find_element_by_xpath("../div/div[2]")
        self.adprize_count = int(adprize.text)
        print("Adprize: %i" % (self.adprize_count))
        if self.adprize_count > 0:
            adprize.click()
            self.driver.switch_to.window(self.driver.window_handles[1])
            self.page = NeobuxPage.AD
            while True:
                print("Adprize remaining: %i   " % (self.adprize_count), end= "\r", flush=True)
                try:
                    header = self.load.until(expected_conditions.element_to_be_clickable(Neobux.AD_HEADER))
                    self.wait.until(expected_conditions.text_to_be_present_in_element(Neobux.AD_HEADER, "Advertisement validated!"))
                    self.load.until(lambda d : header.find_elements_by_link_text("Next"))
                    self.adprize_count = int(header.find_element_by_id("rmnDv").text)
                    next = header.find_element_by_link_text("Next")
                    next.click()
                except TimeoutException:
                    if self.adprize_count == 1:
                        self.adprize_count = 0
                        close = header.find_element_by_link_text("Close")
                        close.click()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                        self.page = NeobuxPage.VIEW
                        break
                    else:
                        input("Press Enter to continue...") #in case something other than nothing happens, I want to catch it for observation

    def __del__(self):
        """Ensure webdriver cleanup upon clicker garbage collection"""
        self.driver.quit()

class NeobuxPage(Enum):
    NONE = ""
    HOME = "home"
    LOGIN = "login" #login page without captcha prompt
    CAPTCHA = "captcha" #login page with captcha prompt
    VERIFICATION = "verification"
    LOGIN_LOG = "login_log"
    DASHBOARD = "dashboard"
    STATISTICS = "statistics"
    VIEW = "view"
    AD = "ad"
    LOGOUT = "logout"

if __name__ == "__main__":
    try:
        clicker = Neobux()
        clicker.launch()
        clicker.prompt_login()
        if clicker.captcha_image:
            clicker.captcha_image.show()
            clicker.prompt_captcha()
        clicker.log_in()
        if clicker.page is NeobuxPage.VERIFICATION:
            clicker.prompt_authentication_number()
            clicker.verify()
        print()
        clicker.view_ads()
        clicker.click_ads()
        print()
        clicker.click_adprize()
    except Exception:
        traceback.print_exc()
        input("Error occurred, press Enter to quit")