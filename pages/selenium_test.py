import streamlit as st
import requests 
from bs4 import BeautifulSoup 
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time


username = "reddiveusa@gmail.com" 
password = "Profit44" 

# Initialize Selenium WebDriver
####driver = webdriver.Chrome()  # Ensure you have the Chrome WebDriver installed
'''
# Step 1: Login to eBay
driver.get('https://www.ebay.com/sh/research?marketplace=EBAY-US&tabName=SOLD')
time.sleep(2)  # Wait for the login page to load


# Find the username field and enter the username
username_field = driver.find_element(By.ID, 'userid')
username_field.send_keys(username)
username_field.send_keys(Keys.RETURN)
time.sleep(2)  # Wait for the password field to load

# Find the password field and enter the password
password_field = driver.find_element(By.ID, 'pass')
password_field.send_keys(password)
password_field.send_keys(Keys.RETURN)
time.sleep(5)  # Wait for the login process to complete

# Step 2: Extract cookies from Selenium and add them to the requests session
session = requests.Session()
for cookie in driver.get_cookies():
    session.cookies.set(cookie['name'], cookie['value'])
'''
# Step 3: Use the session to scrape the desired page
target_url = 'https://www.ebay.com/sh/research?marketplace=EBAY-US&tabName=SOLD'
response = requests.get(target_url)

soup = BeautifulSoup(response.content, 'html.parser')

# Example: Extracting the item title
item_title =  soup.find('h1', attrs={'class': 'pageTitle'})
print('Item Title:', item_title)

# Close the Selenium WebDriver
##driver.quit()