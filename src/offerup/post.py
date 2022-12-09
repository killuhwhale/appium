
import base64
import subprocess
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


FILE_DIR = "/storage/emulated/0/Pictures/offerup"
LOCAL_FILES = "/home/killuh/Pictures/offerup"

# Lanuch Emulator 
# cd ${ANDROID_HOME}/tools && emulator -avd Pixel_2_API_30_PlayStore && cd ~

def poll_reboot():
    # While adb connection is not valid, check adb connection.
    pass


def refresh_mediastore():
    adb_cmd = '''find /storage/emulated/0/Pictures/offerup | while read f; do am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d \"file://${f}\"; done '''
    cmd = ( 'adb', 'shell', adb_cmd)
    outstr = subprocess.run(cmd, check=True, encoding='utf-8',capture_output=True).stdout.strip()
    return outstr


def remove_images():
    '''
        Use Appium API/ ADB to remove all DUT media
    '''
    try:
        
        cmd = ('adb', "shell", "rm", f"{FILE_DIR}/*" )
        outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                                capture_output=True).stdout.strip()
        print(outstr)
        return True
    except Exception as e:
        print("Failed to remove images: ", e)
        return False



def add_images(folder: AnyStr='cooler1'):
    '''
        Use Appium API/ ADB to add images from client host device to DUT
        images: List of paths to images to add.
    '''
    print("Adding images from ", folder)
    cmd = ('ls', f"{LOCAL_FILES}/{folder}")
    outstr = subprocess.run(cmd, check=True, encoding='utf-8',capture_output=True).stdout.strip()
    print("Foudn images: ", outstr)            
    images = []
    num_images = 0
    if "\n" in outstr:
        images = outstr.split("\n")
    else:
        images = outstr
    try:
        for img in images:
            local_path = f'{LOCAL_FILES}/{folder}/{img}'
            ext = img.split(".")[-1]
            print(f"Pusing ({ext}):", local_path, " -> ", FILE_DIR)
            if not ext.lower() in ["png", "jpg", 'jpeg']:
                print(f"bad image: {img}")
                continue
            num_images += 1
            cmd = ( 'adb', 'push', local_path, FILE_DIR)
            outstr = subprocess.run(cmd, check=True, encoding='utf-8',capture_output=True).stdout.strip()
    except Exception as e:
        print("Err: ", e)
    return num_images
            
                                  

# adb push /home/killuh/Pictures/offerup/cooler1/Screenshot\ from\ 2022-11-27\ 12-46-55.png /storage/emulated/0/Pictures





def choose_images(driver: webdriver.Remote, num_images: int):
    '''
        Once the select images screen is open, this will tap the required images.


        Images in DOwnload folder match the order in the APP/

            Downlaods/
                1. img1
                2. img2
                3. img3
                4. img4
                  ....

        To selcet images we get rows of 3 items


        In App:

             1      2    3
        1 [camera, 1st , 2nd]
        2 [3rd, 4th, 5th]
        3 [6th, 7th, 8th]
         ...

         /hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/
         android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/
         android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/
         android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/
         android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/
         android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/
         android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout[1]/android.view.ViewGroup/
         android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/
         android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[3]/android.widget.ScrollView/
         android.view.ViewGroup/

         android.view.ViewGroup[1]/android.view.ViewGroup[2]  <---- This will control which images we want.

         Division integer -> Row
         Modulo integer -> Column

         image 7 => 6 / 3 == 2 r0 -> go 2 full rows, go to cell 1
         image 7 => 7 / 3 == 2 r1 -> go 2 full rows, go to cell 1
         image 7 => 8 / 3 == 2 r2 -> go 2 full rows, go to cell 2
    '''
    # To do write for loop for x rows and 3 columns
    # Open Slect Images
    sleep(2)
    print("Selecting photos")
    el1 = driver.find_element(by=AppiumBy.XPATH, value="/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[3]/android.widget.ScrollView/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.Button[2]")
    el1.click()
    el1.click()
    print("Clicked Select!")

    for i in range(num_images+1):
        y = (i//3) + 1
        x = (i%3) + 1
        if x == 1 and y == 1:
            continue
        # Select Image i
        print("Click pos for image ", y , x)
        el8 = driver.find_element(by=AppiumBy.XPATH, value=f"/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[3]/android.widget.ScrollView/android.view.ViewGroup/android.view.ViewGroup[{y}]/android.view.ViewGroup[{x}]")
        el8.click()
        
    el12 = driver.find_element(by=AppiumBy.XPATH, value="/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.Button")
    el12.click()

    # # Select Image 1
    # el8 = driver.find_element(by=AppiumBy.XPATH, value="/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[3]/android.widget.ScrollView/android.view.ViewGroup/android.view.ViewGroup[1]/android.view.ViewGroup[2]")
    # el8.click()
    # # Select Image 2
    # el9 = driver.find_element(by=AppiumBy.XPATH, value="/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[3]/android.widget.ScrollView/android.view.ViewGroup/android.view.ViewGroup[1]/android.view.ViewGroup[3]")
    # el9.click()
    # # Select Image 3
    # el10 = driver.find_element(by=AppiumBy.XPATH, value="/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[3]/android.widget.ScrollView/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup[1]")
    # el10.click()
    # # Select Image 4
    # el11 = driver.find_element(by=AppiumBy.XPATH, value="/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[3]/android.widget.ScrollView/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup[2]")
    # el11.click()
    # # Press Done
    


def _post_offer(driver: webdriver.Remote, title: AnyStr, desc: AnyStr, price: AnyStr, folder: AnyStr, category: int):
    '''
        Adds Title, description, price and send post.
        Goes throuhg remaining pages.

        Shipping and Location settings must be set.

        There are 4 screens:
        1. Post
        2. Details
        3. Price
        4. Finish

    '''

    remove_images()
    num_images = add_images(folder)
    sleep(2)
    print("Refreshing mediastore")
    refresh_mediastore()



    el1 = driver.find_element(by=AppiumBy.XPATH, value="//android.widget.Button[@content-desc=\"ou-tab-navigator.post, Navigates to the ou-tab-navigator.post screen\"]/android.view.ViewGroup")
    el1.click()
    edit_text_first_page = driver.find_elements(by=AppiumBy.CLASS_NAME, value='android.widget.EditText')
    print("Di we find two buttons? ", len(edit_text_first_page))
    edit_text_first_page[0].click()
    edit_text_first_page[0].send_keys(title)
    driver.back()
    edit_text_first_page[1].click()
    edit_text_first_page[1].send_keys(desc)
    driver.back()

    choose_images(driver, num_images)

    sleep(2)
    # Press Next from First Page 
    print("Pressing next from first page")
    x = "650"
    y = "1704"
    cmd = ( 'adb', 'shell', 'input', 'tap', x, y)
    outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
    print("Tapped!")
    
    
    sleep(2)
    #
    # 2. Details Page
    #
    # category

    category_panel = el19 = driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value="Category")
    category_panel.click()

    #Select Category
    x = "269"
    y = "375"
    cmd = ( 'adb', 'shell', 'input', 'tap', x, y)
    outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
    sleep(2)

    if category == 0:
        pass
        # select Cell Phones
        x = "366"
        y = "659"
        cmd = ( 'adb', 'shell', 'input', 'tap', x, y)
        outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
    elif category == 1:
        # select Computer and Accessories
        x = "412"
        y = "1209"
        cmd = ( 'adb', 'shell', 'input', 'tap', x, y)
        outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
    
    driver.back()
    sleep(2)
    # Select Next to go to Price page
    x = "700"
    y = "1709"
    cmd = ( 'adb', 'shell', 'input', 'tap', x, y)
    outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
    
    sleep(2)
    # Tap Price
    x = "609"
    y = "386"
    cmd = ( 'adb', 'shell', 'input', 'tap', x, y)
    outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
    sleep(2)
    # Input Price
    price = "70"
    cmd = ( 'adb', 'shell', 'input', 'text', price)
    outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
    # Input Price
    sleep(2)
    # Tap Next
    x = "623"
    y = "1092"
    cmd = ( 'adb', 'shell', 'input', 'tap', x, y)
    outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
    
    
    
    #
    # Tap Post
    # x = "524"
    # y = "1709"
    # cmd = ( 'adb', 'shell', 'input', 'tap', x, y)
    # outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
    #
    
    # 4. Finish
    # Shipping Switch
    # ship_switch = driver.find_element(
    #     by=AppiumBy.XPATH, value="/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[3]/android.widget.ScrollView/android.view.ViewGroup/android.view.ViewGroup[4]/android.widget.Switch")
    # is_checked = ship_switch.get_attribute("checked")
    # # Deafults to false, check again after data loads.
    # if (is_checked == 'false'):
    #     sleep(5)
    #     ship_switch = driver.find_element(
    #         by=AppiumBy.XPATH, value="/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[3]/android.widget.ScrollView/android.view.ViewGroup/android.view.ViewGroup[4]/android.widget.Switch")
    #     is_checked = ship_switch.get_attribute("checked")
    # #
    # print("Is Checked", is_checked, type(is_checked))
    # if (is_checked == 'true'):
    #     print()
    #     ship_switch.click()
    #
    # Click Done
    # el25 = driver.find_element(by=AppiumBy.XPATH,
    #                            value="/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.Button")
    # el25.click()


def post_offer(**kwargs):
    # sleep(15)  # Wait for app to start
    driver = kwargs['driver']
    _post_offer(**kwargs)


if __name__ == "__main__":
    pass
