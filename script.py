from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from PIL import Image
from PIL import ImageEnhance
import getpass
import random
import time
import base64
import io

random.seed()
driver = webdriver.Firefox(service_log_path='NUL')
actions = ActionChains(driver)
load = WebDriverWait(driver, 3)
wait = WebDriverWait(driver, 60)
driver.get('https://www.neobux.com/')
login = load.until(expected_conditions.element_to_be_clickable((By.LINK_TEXT, 'Login')))
login.click()
login_form = driver.find_element_by_id('loginform')
input_rows = login_form.find_elements_by_xpath('./table/tbody/tr[1]/td/table/tbody/tr')
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
	ImageEnhance.Brightness(img).enhance(1.5).show()
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
load.until(expected_conditions.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div/table')))
view_ads = load.until(expected_conditions.element_to_be_clickable((By.LINK_TEXT, 'View Advertisements')))
view_ads.click()
load.until(expected_conditions.element_to_be_clickable((By.CLASS_NAME, 'cell')))
ads = driver.find_elements_by_class_name('cell')
header_xpath = '/html/body/table/tbody/tr[1]/td/table/tbody/tr/td/table/tbody/tr/td[1]/table/tbody/tr'
for ad in ads:
	driver.execute_script('return arguments[0].scrollIntoView();', ad)
	actions.move_to_element(ad).perform()
	ad.click()
	load.until(lambda d : 'Click the red dot' in ad.text)
	dot = ad.find_element_by_tag_name('img')
	actions.move_to_element(dot).perform()
	dot.click()
	driver.switch_to.window(driver.window_handles[1])
	header = load.until(expected_conditions.element_to_be_clickable((By.XPATH, header_xpath)))
	if 'You already saw this advertisement' in header.text:
		driver.close()
		driver.switch_to.window(driver.window_handles[0])
		actions = ActionChains(driver)
		continue
	wait.until(expected_conditions.text_to_be_present_in_element((By.XPATH, header_xpath), 'Advertisement validated!'))
	close = header.find_element_by_link_text('Close')
	close.click()
	driver.switch_to.window(driver.window_handles[0])
	actions.reset_actions()
	actions = ActionChains(driver)
adprize = driver.find_element_by_id('adprize').find_element_by_xpath('../div/div/a')
adprize.click()
driver.switch_to.window(driver.window_handles[1])
while true:
	header = load.until(expected_conditions.element_to_be_clickable((By.XPATH, header_xpath)))
	wait.until(expected_conditions.text_to_be_present_in_element((By.XPATH, header_xpath), 'Advertisement validated!'))
	try:
		next = header.find_element_by_link_text('Next')
		next.click()
	except NoSuchElementException:
		close = header.find_element_by_link_text('Close')
		close.click()
		driver.switch_to.window(driver.window_handles[0])
		break
driver.quit()