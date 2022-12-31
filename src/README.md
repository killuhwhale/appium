Example Output

<img src="https://raw.githubusercontent.com/killuhwhale/appium/main/src/images/readme/demo_output.png?sanitize=true&raw=true" />
<video src="https://drive.google.com/open?id=1kztEqXsqcLiEa24NN3vr3_ddeH0D0re4&authuser=0&usp=drive_link" />


# Need to test on Chromebook
Need to understand if devices will have preinstalled accounts
    - Need accounts like testminnie001@gmail.com logged into device
    - 

Problems:



com.google.android.contacts
- wont uninstall
    Makes the beginning uninstall check take a long time


TODO:


- Detect 'bad' chars -> ó
    - Adb shell struggles to send these.
    - Need to find a solution

Features/ Optimizations:
- Get size of an app to anticipate download time



# NOTES

# https://github.com/appium/appium-uiautomator2-driver#driverserver
#   - appium:skipServerInstallation => Improve startup speed if we know UIAutomator is already installed...

# TODO
# Need to identify each device so we can use the correct commands
# So far Pixel 2 and Chromebook Coachz have different View Names
#   - Chromebooks views are obfuscated
# We can use this to get deviceInfo
# https://github.com/appium/appium-uiautomator2-driver#mobile-deviceinfo
# self.driver.execute_script("mobile: scroll", {'direction': 'down'})
# self.driver.execute_script("mobile: acceptAlert", {'buttonLabel': 'Accept'})
# self.driver.execute_script("mobile: dismissAlert", {'buttonLabel': 'Dismiss'})
# self.driver.execute_script("mobile: deviceInfo", {})

# self.driver.execute_script("mobile: activateApp", {appId: "my.app.id"})
    # Activates the given application or launches it if necessary. The action literally simulates clicking the corresponding application icon on the dashboard.

# self.driver.execute_script("mobile: changePermissions", {
#                                   permissions: 'all',
#                                   appPackage: '',
#                                   action: 'allow',
# })
#  mobile: 

