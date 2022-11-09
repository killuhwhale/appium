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
    driver.implicitly_wait() # only needs to be called once per session

    get_screen_name = ""
    btns = driver.find_elements(
        by=AppiumBy.CLASS_NAME, value='android.widget.Button')
    print("Btns", btns)

    view_groups = driver.find_elements(
        by=AppiumBy.CLASS_NAME, value='android.view.ViewGroup')
        
    view_groups = [vg for vg in view_groups if vg.get_attribute("clickable") == 'true']
    print("Viewgroups", view_groups)

    all_btns['screen_1'].extend(btns)  # Colllect all buttons for a given activity/ screen.

    # Possibly keep a set of all elements we have found,
    #  When a click a new page, we search for elements we havent found.
    #    The page source will likely have old ViewGroups, if we click a page
    #       and do not find a ney elements to add, we probably havent waited long enough for the new page to load.
    #           If this becomes  a problem, we can use this tracking idea using a set.



    # First test run, I was successfully able to click and open each view
    # pressing the system back key after each view was opened.
    # Seems somewhat promising...
    for v in view_groups:
        v.click()
        # Find new elements loop here...
        v.find_elements(AppiumBy.CLASS_NAME, value='android.view.ViewGroup')
        # Take advatage of the implicit wait.
        driver.back()
        sleep(2)

            
