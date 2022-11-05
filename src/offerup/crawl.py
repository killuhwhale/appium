from collections import defaultdict
from time import sleep
from typing import AnyStr, List
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from utils.utils import android_des_caps
from selenium.common.exceptions import WebDriverException

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput


'''
Testing strategy....

1. Crawl until we find enough information to consider this pass or fail
2. Crawl until we find:
    - a TextField
    - a button
    - ea activity that shares the same package name.
        - offer up only has 1 activity called Main, its a react native app
            - it uses other natve activities such as FB and Stripe to handle Auth or Payments...
                - we probably do need to test this for O4C/ mobile/ borken status
    


Hard stuff to consider:
React native apps w/ only 1 activity or varying activities like FaceBook.
    - Each activity may have different layout options that might cause Portfolio only.
        - Must check ea activity.
    - 
Crawling, typically we crawl for URLS to find ea page.
For apps, we click various buttons.
    - Some buttons do not go to anew page
        - They might:
            - Open a modal
            - toggle state on page
            - submit a form
            - navigate
    
    - Maybe we dont need to crawl much...
        We just launch ea activity
            - Look for all displayed elements:
                - InputView
                - ButtonView
                - Take a screent shot analyze.
            
'''


all_btns = defaultdict([])


def crawl(driver: webdriver.Remote):
    '''
        On a given screen, collect all displayed btns.
        Store all buttons under this Screen.
        Click buttons on this screen and recurse
    '''
    get_screen_name = ""
    btns = driver.find_elements(
        by=AppiumBy.CLASS_NAME, value='android.widget.Button')
    print("Btns", btns)

    all_btns['screen_1'].extend(btns)

    for btn in btns:
        print(btn.text)
        print(btn.get_attribute("displayed"))
        print(btn.get_attribute("displayed"))
        print(btn.get_attribute("displayed"))
        print(btn.get_attribute("displayed"))
        print(btn.get_attribute("displayed"))
