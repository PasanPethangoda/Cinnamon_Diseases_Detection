from selenium import webdriver  # type: ignore
from selenium.webdriver.common.by import By  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
from selenium.webdriver.support import expected_conditions as EC  # type: ignore
import os
import time

# Set up WebDriver
driver = webdriver.Chrome()
driver.get("http:/127.0.0.1:5000")
print(driver.title)
driver.quit()