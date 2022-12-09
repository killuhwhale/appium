import collections
from collections import defaultdict
from time import sleep
from typing import AnyStr, Dict, List

import hashlib

from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import (StaleElementReferenceException,
                                        WebDriverException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput

from utils.utils import android_des_caps
from xmldiff import main

main.diff_texts


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


    all_views = collections.defaultdict(str)
    views_to_check = view_groups
    # First test run, I was successfully able to click and open each view
    # pressing the system back key after each view was opened.
    # Seems somewhat promising...
    while True:
        view_groups = views_to_check
        views_to_check = []
        for v in view_groups:
            v.click()
            # Find new elements loop here...
            # Now new page source is loaded, with buttons visible

            for new_v in v.find_elements(AppiumBy.CLASS_NAME, value='android.view.ViewGroup'):
                if not new_v in all_views:
                    views_to_check.append(new_v)
                    all_views[new_v] = 1
            
            # Take advatage of the implicit wait.
            driver.back()
            sleep(2)



# Recusive, when falling back down the callstack we would want to 
        #   go back if only the click() action moved us to a new view. 
        #    If we did not go to a new view, we want to undo what ever action was performed
        #      like close a modal, 
        # Problem, how do we know what action a given view performs?
        # Another problem, what happens when a clickable elment opens an Intent?
        # Opens an Ad in web browser?
        #   - we lose focus of window
        

def filter_clickable(driver: webdriver.Remote, all_views: Dict):
    print("Finding all ViewGruops")
    view_groups = driver.find_elements(
        by=AppiumBy.CLASS_NAME, value='android.view.ViewGroup')
    
    print("Filtering all ViewGruops")
    res = []
    # return [vg for vg in view_groups if vg.get_attribute("clickable") == 'true']
    for vg in view_groups:
        try:
            if not vg.get_attribute("resourceId") in all_views:
                all_views[vg.get_attribute("resourceId")] = 1
                if vg.get_attribute("clickable") == 'true':
                    res.append(vg)
        except StaleElementReferenceException as e:
            print("Error", e, "\n", f"Bad ele ID: ", vg.get_attribute("resourceId"))
    return res

# Take ScreenShot to compare later once we come back to this frame
# Take new screen shot, determine:
#   - How different the two images are
#       - If the page is so different, we may be able to deduct a new page, press back button

#   - See if a new close btn or 'X' icon is showing....
#           - If something just opened, we can just close it
def r_crawl(driver: webdriver.Remote, all_views: Dict, depth: int):
    clickable_views = filter_clickable(driver, all_views)
    print("Found clicked views", clickable_views, "\n")
    for i, v in enumerate(clickable_views):
        print(f"{depth}, {i} Clicked view", v)
        try:
            v.click()  # new screen
            print("Crawling on new view \n")
            input("Before")                                                                                                 
            r_crawl(driver, all_views, depth + 1)
            
            # we can undo that action 

            # here on a new screen, we want press back key
            input("After, we need to know how to undo the action on this call frame")
        except StaleElementReferenceException as e:
            print("Error clicking? ", e)
            print('Going back')
            # driver.back()



def hash_src():
    return hashlib.md5(driver.page_source.encode()).hexdigest()

'''

In addition to a crawling bot, we can also perform specific tasks using image recognition

If fast enough, after each button press we can compare images.
    - If images are very similar, we didnt go to a new page
    - If images vary by certain amount, we have gone to a new page.

Detect (Specific Icons) 
    - Camera Icons
    - Share Icons






1. Starting on MainActivity we gather all clickable element types.
    - View - clickable
    - Buttons 

2. With the current list of clickable elements
    - Click element

3. Result of clicked element
    - a Modal pops up
        - Essentailly a new screen but current activity. Fragments, RN SPA
    - b Some visual or data state is toggled
    - c App navigates to new screen
    - d App navigates back to previous screen
    - e App opens new intent.

    
    Each case will produce new source code.
        - Hashing might not work well if every button produces new source code.

3a. Close pop up
3b. Do nothing
3c. Crawl
3d. Avoid going back (until current page elements are searched.)
3e. Go back top app



How do we detect what the button does?
    - Image recognition

    - Ignore it, and figure out a method to track old views (below)






dict(list)
{
    srcHash:  [views_to_click]
}




**If we can find a way to detect what actions has been done, we can undo that action during the crawl


Tracking old views:
    - Get current src
    - Check if we have seen current source 
        - Huge problem:
            - Src is different on every click, if a single attr changes, hashed src is different

    - if not seen current src
        - Get btns on current src
        - If btns not in globally stored views
            - Hash current source
                - Store Views to click at this current source
            - Store Views found globally
            - Remove current btn from current hashed src btn list
            - Click button
        - return

    -else if seen current src
        - get btn from list
        - remove from list
        - click btn

METHODS to Compare App State
    - Compare XML differences
    - Build Image recognition to detect close buttons
        - https://www.flaticon.com/search/3?word=close&order_by=4
        - we can count the number of close buttons before and after.
            - We can close whatever was opened.
    



'''


def cmp_xml(a, b):
    return main.diff_texts(a, b, diff_options={'F': 0.5, 'ratio_mode': 'fast'})

a = driver.page_source
b = driver.page_source
len(cmp_xml(a.encode(),b.encode()))

# Frame layouts might be useful, at least in OfferUp, framelayouts seem tto be new screen on same activity....



r_crawl(driver, collections.defaultdict(str), 0)