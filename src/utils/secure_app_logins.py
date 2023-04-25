from time import sleep
from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from playstore.app_login_results import AppLoginResults
from utils.app_utils import close_save_password_dialog




def login_netflix(driver: Remote, email: str, password: str) -> bool:
    ''' Secure Flag is set, login by views.
    '''

    sleep(5)  # Give app some time to load and prompt user with Previous saved password.
    # content-desc Cancel
    try:
        try:
            content_desc = "Cancel"
            driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value=content_desc).click()
        except Exception as error:
            print("Previous saved password continue did not appear...")


        # Click 'SIGN IN' button.
        val = "SIGN IN"
        content_desc = f'''new UiSelector().className("android.widget.Button").text("{val}")'''
        driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc).click()


        # id android:id/autofill_dataset_picker
        # class  android.widget.FrameLayout
        # resource-id    android:id/autofill_dataset_picker
        # Autofill Picker is showing no other views are given...

        try:
            val = "android:id/autofill_dataset_picker"
            driver.find_element(by=AppiumBy.ID, value=val)
            driver.back()
        except Exception as error:
            print("Autofill setting are not opened, skipping back().")


        val = "Email or phone number"
        content_desc = f'''new UiSelector().className("android.widget.EditText").text("{val}")'''
        driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc).send_keys(email)

        val = "Password"
        content_desc = f'''new UiSelector().className("android.widget.EditText").text("{val}")'''
        driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc).send_keys(password)

        # Click sign in on page after creds are entered
        val = "Sign In"
        content_desc = f'''new UiSelector().className("android.widget.Button").text("{val}")'''
        driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=content_desc).click()
        sleep(3)
        close_save_password_dialog(driver)
        return AppLoginResults(email_logged_in=True, has_email=True)
    except Exception as error:
        print("Eroor signing into netflix...", error)

    return AppLoginResults()


SECURE_APPS = {
    "com.netflix.mediaclient": login_netflix,
}