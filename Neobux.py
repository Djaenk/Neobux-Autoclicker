from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException

from PIL import Image
from PIL import ImageEnhance

import getpass
import base64
import io
import os

class Neobux:

	_AD_HEADER = (By.XPATH, '/html/body/table/tbody/tr[1]/td/table/tbody/tr/td/table/tbody/tr/td[1]/table/tbody/tr')
	_LOGIN_ROWS_XPATH = './table/tbody/tr[1]/td/table/tbody/tr'
	_DASHBOARD = (By.XPATH, '/html/body/div[2]/div/table')

	def __init__(self):
		self.driver_type = None
		if not self.driver_type:
			try:
				self.driver = webdriver.Firefox(service_log_path = os.path.devnull)
				self.driver_type = 'geckodriver'
			except WebDriverException:
				self.driver_type = None
		if not self.driver_type:
			try:
				self.driver = webdriver.Chrome(service_log_path = os.path.devnull)
				self.driver_type = 'chromedriver'
			except WebDriverException:
				self.driver_type = None
		if not self.driver_type:
			self.driver = webdriver.PhantomJS(service_log_path = os.path.devnull)
			self.driver_type = 'ghostdriver'
		self.actions = ActionChains(self.driver)
		self.load = WebDriverWait(self.driver, 3)
		self.wait = WebDriverWait(self.driver, 60)
		self.stale_ad_count = 0
		self.fresh_ad_count = 0
		self.adprize_count = 0

	def action_click(self, element):
		self.driver.execute_script('return arguments[0].scrollIntoView();', element)
		self.actions.move_to_element(element).perform()
		element.click()

	def launch(self):
		self.driver.get('https://www.neobux.com/')
		login = self.load.until(expected_conditions.element_to_be_clickable((By.LINK_TEXT, 'Login')))
		login.click()
		self.load.until(expected_conditions.element_to_be_clickable((By.ID, 'loginform')))

	def log_in(self):
		while self.driver.find_elements_by_id('loginform'):
			login_form = self.driver.find_element_by_id('loginform')
			input_rows = login_form.find_elements_by_xpath(Neobux._LOGIN_ROWS_XPATH)
			username_input = input_rows[0].find_element_by_xpath('./td/input[@placeholder="Username"]')
			password_input = input_rows[1].find_element_by_xpath('./td/input[@placeholder="Password"]')
			secondary_password_input = input_rows[2].find_element_by_xpath('./td/input[@placeholder="Secondary Password"]')
			username = input('Username: ')
			password = getpass.getpass()
			secondary_password = getpass.getpass('Secondary Password: ')
			if len(input_rows) == 4:
				captcha = input_rows[3].find_element_by_xpath('./td/table/tbody/tr/td[@align="right"]/img')
				captcha_input = input_rows[3].find_element_by_xpath('./td/table/tbody/tr/td[@align="left"]/input')
				src = captcha.get_attribute('src')
				base64_data = src.replace('data:image/png;base64,', '')
				data = base64.b64decode(base64_data)
				img = Image.open(io.BytesIO(data))
				img = ImageEnhance.Brightness(img).enhance(1.5)
				img = ImageEnhance.Contrast(img).enhance(1.5)
				img = ImageEnhance.Sharpness(img).enhance(1.2)
				img.show()
				solution = input("CAPTCHA: ")
				captcha_input.send_keys(solution)
			send = login_form.find_element_by_link_text('send')
			username_input.click()
			username_input.send_keys(username)
			password_input.click()
			password_input.send_keys(password)
			secondary_password_input.click()
			secondary_password_input.send_keys(secondary_password)
			send.click()
		self.load.until(expected_conditions.element_to_be_clickable(Neobux._DASHBOARD))

	def view_ads(self):
		view = self.driver.find_element_by_link_text('View Advertisements')
		view.click()
		self.load.until(expected_conditions.element_to_be_clickable((By.CLASS_NAME, 'cell')))

	def click_ads(self):
		ads = self.driver.find_elements_by_class_name('cell')
		for ad in ads:
			self.action_click(ad)
			self.load.until(lambda d : 'Click the red dot' in ad.text)
			dot = ad.find_element_by_tag_name('img')
			self.action_click(dot)
			self.driver.switch_to.window(self.driver.window_handles[1])
			header = self.load.until(expected_conditions.element_to_be_clickable(Neobux._AD_HEADER))
			if 'You already saw this advertisement' in header.text:
				self.stale_ad_count += 1
				self.driver.close()
				self.driver.switch_to.window(self.driver.window_handles[0])
				adprize = self.driver.find_element_by_id('adprize').find_element_by_xpath('../div/div[2]')
				self.adprize_count = int(adprize.text)
				self.actions = ActionChains(self.driver)
				continue
			self.wait.until(expected_conditions.text_to_be_present_in_element(Neobux._AD_HEADER, 'Advertisement validated!'))
			close = header.find_element_by_link_text('Close')
			close.click()
			self.fresh_ad_count += 1
			self.driver.switch_to.window(self.driver.window_handles[0])
			self.actions.reset_actions()
			self.actions = ActionChains(self.driver)

	def click_adprize(self):
		adprize = self.driver.find_element_by_id('adprize').find_element_by_xpath('../div/div[2]')
		self.adprize_count = int(adprize.text)
		if self.adprize_count == 0:
			return
		adprize.click()
		self.load.until(expected_conditions.staleness_of(adprize))
		self.driver.switch_to.window(self.driver.window_handles[1])
		while self.adprize_count > 0:
			header = self.load.until(expected_conditions.element_to_be_clickable(Neobux._AD_HEADER))
			self.wait.until(expected_conditions.text_to_be_present_in_element(Neobux._AD_HEADER, 'Advertisement validated!'))
			try:
				next = header.find_element_by_link_text('Next')
				next.click()
			except NoSuchElementException:
				close = header.find_element_by_link_text('Close')
				close.click()
				self.driver.switch_to.window(self.driver.window_handles[0])
				break

	def run(self):
		self.launch()
		self.log_in()
		self.view_ads()
		self.click_ads()
		self.click_adprize()

	def __del__(self):
		self.driver.quit()
