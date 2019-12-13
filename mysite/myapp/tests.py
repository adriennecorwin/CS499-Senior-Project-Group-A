# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

# Create your tests here.
from selenium import webdriver
import time
import pytest

# Sets up browser for testing
@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--test-type')
    driver = webdriver.Chrome(options=options)
    driver.get('https://supreme-court-twitter.herokuapp.com/')
    driver.implicitly_wait(10)
    yield driver

def test_signup(driver):
    signup = driver.find_element_by_xpath("//a[@href='/signup/']")
    signup.click()

    assert (driver.current_url == 'https://supreme-court-twitter.herokuapp.com/signup/')

def test_adminlogin(driver):
    username = driver.find_element_by_xpath("//input[@name='username']")
    username.send_keys('admin')

    password = driver.find_element_by_xpath("//input[@name='password']")
    password.send_keys('password')

    login = driver.find_element_by_xpath("//button[@type='submit']")
    login.click()

    assert (driver.current_url == 'https://supreme-court-twitter.herokuapp.com/')

# Test search function with AND selected
# Should return tweets including all search queries
def test_andsearch(driver):
    and_button = driver.find_element_by_xpath("//span[text()='AND']")
    and_button.click()
    
    users = driver.find_element_by_xpath("//input[@name='users']")
    users.send_keys('malbertnews')

    hashtag = driver.find_element_by_xpath("//input[@name='hashtags']")
    hashtag.send_keys('SCOTUS')

    keywords = driver.find_element_by_xpath("//input[@name='keywords']")
    keywords.send_keys('Supreme Court')

    ''''date_from = driver.find_element_by_xpath("//input[@name='from']")
    date_from.click()
    day = driver.find_element_by_xpath("//button[@data-day='1']")
    day.click()
    ok_button = driver.find_element_by_xpath("//button[text()='OK']")
    ok_button.click()'''

    search_button = driver.find_element_by_xpath("//button[@name='search']")
    search_button.click()

    assert (driver.find_element_by_xpath("//h6[contains(text(), '#SCOTUS')]") and driver.find_element_by_xpath("//h6[contains(text(), 'Supreme Court')]") and driver.find_element_by_xpath("//a[@href='http://www.twitter.com/malbertnews']"))


# Tests search function with OR selected
# Should return tweets with at least one of the search queries
def test_orsearch(driver):
    or_button = driver.find_element_by_xpath("//span[text()='OR']")
    or_button.click()

    users = driver.find_element_by_xpath("//input[@name='users']")
    users.send_keys("malbertnews")

    hashtag = driver.find_element_by_xpath("//input[@name='hashtags']")
    hashtag.send_keys("SCOTUS")

    keywords = driver.find_element_by_xpath("//input[@name='keywords']")
    keywords.send_keys("Supreme Court")

    '''date_from = driver.find_element_by_xpath("//input[@name='from']")
    date_from.click()
    day = driver.find_element_by_xpath("//button[@data-day='1']")
    day.click()
    ok_button = driver.find_element_by_xpath("//button[text()='OK']")
    ok_button.click()'''

    search_button = driver.find_element_by_xpath("//button[@name='search']")
    search_button.click()

    assert (driver.find_element_by_xpath("//h6[contains(text(), '#SCOTUS')]") or driver.find_element_by_xpath("//h6[contains(text(), 'Supreme Court')]") or driver.find_element_by_xpath("//a[@href='http://www.twitter.com/malbertnews']"))

# Tests expanding tweet details
# Should confirm tweet details are shown
def test_details(driver):
    expand_button = driver.find_element_by_xpath("//i[text()='more_vert']")
    expand_button.click()

    assert driver.find_element_by_xpath("//div[@class='card-reveal'][@style='display: block; transform: translateY(-100%);']")

# Tests link to user profile
# Should open user's profile on Twitter
def test_link(driver):
    user_link = driver.find_element_by_xpath("//a[@target='_blank']")
    user_link.click()

    driver.switch_to.window(driver.window_handles[1])
    assert 'twitter.com' in driver.current_url

# Tests clicking refresh function
# Should return to homepage
def test_refresh(driver):
    url = driver.current_url
    refresh_button = driver.find_element_by_xpath("//i[text()='refresh']")
    refresh_button.click()

    assert (driver.current_url == url)

# Tests download csv file function
# Should download a csv file of tweets
def test_download(driver):
    url = driver.current_url
    download_button = driver.find_element_by_xpath("//i[text()='file_download']")
    download_button.click()

    confirm_button = driver.find_element_by_xpath("//button[@type='submit'][@name='download']")
    confirm_button.click()

    assert (driver.current_url == url)

# Tests pagination
# Should click on 2 and go to second page, click on next page and go to third page
def test_pagination(driver):
    pagetwo = driver.find_element_by_xpath("//a[@class='pagination-number'][@href='?page=2']")
    pagetwo.click()

    assert driver.find_element_by_xpath("//span[@class='pagination-number pagination-current'][text()='2']")

    next_page = driver.find_element_by_xpath("//a[@class='pagination-action'][@href='?page=3']")
    next_page.click()
    driver.implicitly_wait(2)

    assert driver.find_element_by_xpath("//span[@class='pagination-number pagination-current'][text()='3']")

# Tests changing twitter search query
# Should confirm new keyword is added to search query
def test_edit(driver):
    url = driver.current_url

    change_button = driver.find_element_by_xpath("//a[@id='change-query-btn']")
    change_button.click()

    keywords = driver.find_element_by_xpath("//input[@name='pull-keywords']")
    keywords.clear()
    keywords.send_keys('Supreme Court')

    submit_button = driver.find_element_by_xpath("//button[@name='change']")
    submit_button.click()

    assert (driver.current_url == url) 

    change_button = driver.find_element_by_xpath("//a[@id='change-query-btn']")
    change_button.click()

    assert driver.find_element_by_xpath("//input[@name='pull-keywords'][@value='Supreme Court']")

def test_logout(driver):
    logout = driver.find_element_by_xpath("//a[text()='Logout']")
    logout.click()

    assert (driver.current_url == 'https://supreme-court-twitter.herokuapp.com/login/')

def test_userlogin(driver):
    username = driver.find_element_by_xpath("//input[@name='username']")
    username.send_keys('test')

    password = driver.find_element_by_xpath("//input[@name='password']")
    password.send_keys('cs499rocks')

    login = driver.find_element_by_xpath("//button[@type='submit']")
    login.click()

    assert (driver.current_url == 'https://supreme-court-twitter.herokuapp.com/')

def test_userpage(driver):
    assert (not driver.find_element_by_xpath("//a[@id='change-query-btn']"))

# Cleans up after tests
def test_quit(driver):
    driver.close()