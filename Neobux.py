import os

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
    if url is "https://www.neobux.com/":
        return NeobuxPage.HOME
    if "https://www.neobux.com/m/l/" in url:
        return NeobuxPage.LOGIN
    if "https://www.neobux.com/m/ga/" in url:
        return NeobuxPage.VERIFICATION
    if "https://www.neobux.com/m/tta/" in url:
        return NeobuxPage.LOGIN_LOG
    if "https://www.neobux.com/c/" in url:
        return NeobuxPage.DASHBOARD
    if "https://www.neobux.com/m/v/" in url:
        return NeobuxPage.VIEW
    if "https://www.neobux.com/v/" in url:
        return NeobuxPage.AD
    if "https://www.neobux.com/m/l0/" in url:
        return NeobuxPage.LOGOUT
    return -1

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
    LOGIN_ROWS_XPATH = "./table/tbody/tr[1]/td/table/tbody/tr" #relative to the login form
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

    def __init__(self, driver_type = None, threading = False, connection = None):
        """Creates a selenium webdriver
        
        Initializes the webdriver, using a webdriver of the type specified. If
        no driver type is specified, attempts to start a Firefox session, then
        a Chrome session if Firefox fails, then defaults to PhantomJS if Chrome
        fails. After initialization of webdriver, launches Neobux site.

        The threading argument can be passed a truthy value to make the
        instance run its methods in another thread. This is to allow access to
        instance variables while a function is executing. However, to protect
        the webdriver, some methods manipulating it are synchronous even when
        run in threads and will block other methods that manipulate the driver.

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
                #options.headless = True
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
        self.wait = WebDriverWait(self.driver, 60)

        #clicker setup
        self.page = NeobuxPage.NONE
        self.username = ""
        self.password = ""
        self.secondary_password = ""
        self.captcha_image = None
        self.captcha_key = ""
        self.authentication_number = ""
        self.login_error = None
        self.ad_count = 0
        self.stale_ad_count = 0
        self.fresh_ad_count = 0
        self.adprize_count = 0

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
        #check 
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
        if self._threading:
            threading.Timer(0.1, self._assign_threads).start()

    def mainloop(self):
        """Runs an infinite loop, enters operation via the connection

        The instance enters an infinite loop. From within the loop, operations
        are performed by sending instructions in the form of tuples.

        To set or retrieve a data attribute, the first element of the tuple
        must be the string "data". The second element of the tuple must be a
        string containing the name of the desired attribute. If there exists a
        third element, then it is assigned to the specified data attribute. If
        not, then the value of the data attribute is sent back through the
        pipe.

        To invoke an instance method, the first element of the tuple must be
        the string "method". The second element must be a string containing
        name of the method. All following elements, if any, will be passed to
        the method as arguments. If the invoked method returns a value, that
        value is sent back through the pipe.

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
        
        timeout = 0.1
        while True:
            if self._connection.poll(timeout):
                instruction = self._connection.recv()
            else:
                continue
            if isinstance(instruction, tuple):
                if instruction[0] is "data":
                    if hasattr(self, instruction[1]):
                        if len(instruction) == 2:
                            value = getattr(self, instruction[1])
                            self._connection.send(value)
                        else:
                            setattr(self, instruction[1], instruction[2])
                    elif instruction[1] is timeout:
                        if len(instruction) == 2:
                            self._connection.send(timeout)
                        else:
                            timeout = instruction[2]
                    else:
                        raise ValueError("Invalid instruction: No such data attribute")
                elif instruction[0] is "method":
                    if hasattr(self, instruction[1]):
                        function = getattr(self, instruction[1])
                        args = instruction[2:]
                        retval = function(*args)
                        if retval is not None:
                            self._connection.send(retval)
                    elif instruction[1] is "exit_loop":
                        break
                    else:
                        raise ValueError("Invalid instruction: No such method")
                else:
                    raise ValueError("Invalid instruction: data or method instruction not specified")
            else:
                raise TypeError("Invalid instruction: not of class tuple")
            instruction = None

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
        if not connection:
            self._connection = None
        else:
            raise TypeError("argument is not a multiprocessing.connection.Connection object")

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
        self.username = input("Username: ")
        self.password = getpass.getpass()
        self.secondary_password = getpass.getpass("Secondary Password: ")

    def prompt_captcha(self, targeted = False):
        """Prompts the user for the captcha key from the command line"""
        #if self._threading and not targeted:
        #    self._nonblocking_threads.append((self.prompt_captcha, True))
        #    return
        self.captcha_key = input("Verification Code: ")

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
        input_rows = login_form.find_elements_by_xpath(Neobux.LOGIN_ROWS_XPATH)
        if len(input_rows) == 4:
            captcha = input_rows[3].find_element_by_xpath("./td/table/tbody/tr/td[@align='right']/img")
            captcha_input = input_rows[3].find_element_by_xpath("./td/table/tbody/tr/td[@align='left']/input")
            src = captcha.get_attribute("src")
            base64_data = src.replace("data:image/png;base64,", "")
            self.captcha_image = Image.open(BytesIO(b64decode(base64_data)))
            #self.captcha_image = Image.composite(self.captcha_image, Image.new("RGB", self.captcha_image.size, "white"), self.captcha_image)
        else:
            self.captcha_image = None

    def log_in(self, targeted = False):
        """Attempts to log in to Neobux using the instance username/password/key values"""
        if self._threading and not targeted:
            self._blocking_threads.put((self.log_in, True))
            return
        if self.page is not NeobuxPage.LOGIN:
            raise RuntimeError("Can only attempt to log in from the Neobux Login page")
        login_form = self.driver.find_element_by_id("loginform")
        input_rows = login_form.find_elements_by_xpath(Neobux.LOGIN_ROWS_XPATH)
        username_input = input_rows[0].find_element_by_xpath("./td/input[@placeholder='Username']")
        password_input = input_rows[1].find_element_by_xpath("./td/input[@placeholder='Password']")
        secondary_password_input = input_rows[2].find_element_by_xpath("./td/input[@placeholder='Secondary Password']")
        if self.captcha_image:
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
            self.load.until(lambda driver : "https://www.neobux.com/m/l/" not in driver.current_url)
            self.login_error = None
            self.captcha_image = None
            self.page = _discern_page(self.driver)
        except TimeoutException:
            if self.driver.find_elements_by_xpath(Neobux.ERROR_MESSAGE_XPATH):
                self.login_error = driver.find_element_by_xpath(Neobux.ERROR_MESSAGE_XPATH).find_element_by_xpath("..").text
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
        self.ad_count = len(self.driver.find_elements_by_class_name("cell"))
        print("Available advertisements: %i" % (self.ad_count))

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
        ads = self.driver.find_elements_by_class_name("cell")
        for ad in ads:
            print("stale ads: %i, clicked ads: %i" % (self.stale_ad_count, self.fresh_ad_count), end= "\r", flush=True)
            _action_click(self.driver, self.actions, ad)
            self.load.until(lambda d : "Click the red dot" in ad.text)
            dot = ad.find_element_by_tag_name("img")
            _action_click(self.driver, self.actions, dot)
            self.driver.switch_to.window(self.driver.window_handles[1])
            self.page = NeobuxPage.AD
            header = self.load.until(expected_conditions.element_to_be_clickable(Neobux.AD_HEADER))
            if "You already saw this advertisement" in header.text:
                self.stale_ad_count += 1
                self.driver.close()
            else:
                self.wait.until(expected_conditions.text_to_be_present_in_element(Neobux.AD_HEADER, "Advertisement validated!"))
                close = header.find_element_by_link_text("Close")
                close.click()
                self.fresh_ad_count += 1
            self.driver.switch_to.window(self.driver.window_handles[0])
            self.page = NeobuxPage.VIEW
            try:
                adprize = self.driver.find_element_by_id("adprize").find_element_by_xpath("../div/div[2]")
                self.adprize_count = int(adprize.text)
            except NoSuchElementException:
                self.adprize_count = 0
            self.actions.reset_actions()
            self.actions = ActionChains(self.driver)
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
    NONE = 0
    HOME = 1
    LOGIN = 2
    VERIFICATION = 3
    LOGIN_LOG = 4
    DASHBOARD = 5
    VIEW = 6
    AD = 7
    LOGOUT = 8

if __name__ == "__main__":
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
    clicker.view_ads()
    clicker.click_ads()
    clicker.click_adprize()