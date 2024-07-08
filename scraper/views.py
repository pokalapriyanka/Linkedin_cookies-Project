from django.shortcuts import render,redirect

# Create your views here.
import os
import json
import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException,WebDriverException
from bs4 import BeautifulSoup
from .models import Message

# Initialize WebDriver with options
def init_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-webgl')  # Disable WebGL to avoid GPU stall errors
    options.add_argument('--log-level=3')  # Suppress console warnings and errors
    driver = webdriver.Chrome(options=options)
    return driver

# Load cookies if they exist
def load_cookies(driver, cookies_file):
    if os.path.exists(cookies_file):
        with open(cookies_file, 'r') as file:
            cookies = json.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)

# Save cookies to a file
def save_cookies(driver, cookies_file):
    with open(cookies_file, 'w') as file:
        json.dump(driver.get_cookies(), file)

# Scrape contact details
def scrape_details(message):
    emails = re.findall(r'\S+@\S+', message)
    phones = re.findall(r'\b\d{10}\b', message)
    links = re.findall(r'http[s]?://\S+', message)
    return emails, phones, links

# Retry mechanism for network requests
def retry_request(driver, url, retries=3):
    for i in range(retries):
        try:
            driver.get(url)
            return
        except WebDriverException:
            if i == retries - 1:
                raise
            time.sleep(2)

# Scrape LinkedIn messages
def scrape_linkedin(request):
    cookies_file = 'linkedin_cookies.json'
    driver = init_driver()
    retry_request(driver, "https://www.linkedin.com/login")

    # Wait for manual 2FA completion
    input("Press Enter after completing the 2FA process...")

    # Save cookies for future sessions
    save_cookies(driver, cookies_file)

    # Navigate to messages
    retry_request(driver, "https://www.linkedin.com/messaging/")
    time.sleep(5)

    # Click on the first message
    message_threads = driver.find_elements_by_css_selector('ul.msg-conversations-container__conversations-list li')
    for thread in message_threads:
        thread.click()
        time.sleep(2)

        # Scroll through the message history
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Parse message history
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        messages = soup.find_all('div', class_='msg-s-message-list-content')

        for message in messages:
            message_text = message.get_text()
            emails, phones, links = scrape_details(message_text)
            Message.objects.create(
                profile_name=thread.text,
                emails=', '.join(emails),
                phones=', '.join(phones),
                links=', '.join(links)
            )

    driver.quit()
    return redirect('scrape_results')

# View to display scrape results
def scrape_results(request):
    messages = Message.objects.all()
    return render(request, 'results.html',{'messages':messages})
