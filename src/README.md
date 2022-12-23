Example Output

<img src="https://raw.githubusercontent.com/killuhwhale/appium/main/src/images/readme/playstore_output.png?sanitize=true&raw=true" />
<video src="https://raw.githubusercontent.com/killuhwhale/appium/main/src/images/readme/DEMO_APPIUM.MOV?sanitize=true&raw=true" />


# Need to test on Chromebook
Need to understand if devices will have preinstalled accounts
    - Need accounts like testminnie001@gmail.com logged into device
    - 

Problems:

All ADB commands must have a transport id associated with them....
- If more than 1 adb device is connected, it breaks, Need to add -t transport_id for device we are targeting
- Create a method to get the transport Ip based on deviceName/ ip


com.google.android.contacts
- wont uninstall
    Makes the beginning uninstall check take a long time


TODO:


- Detect 'bad' chars -> ó
    - Adb shell struggles to send these.
    - Need to find a solution

- Detect Platstore in Foreground before each app search/install loop
    -   Someitmes playstore crashes or isnt in the foreground and this will affect the loop
        - We should check and retore the playstore, at least once, at the beginning of the loop
            - Depedning on how fast this check is, we can check befre each step during the search/install phase.

- Find a reliable way to wait for current activity to be loaded when opening an app...
    - Games sometimes take a while to load/ download extra data
     - This is a difficult task
        - Even knowing the activity to wait for, it only lets us know when the activity is done  loaded, not the content within the activity.

-  Create architecture to create multiple Drivers and start a job for each one. 
    - Currently, in main.py, we are just creating one driver.



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
# self.driver.execute_script("mobile: queryAppState", {appId: "my.app.id" })
    # The app is not installed: 0
    # The app is installed and is not running: 1
    # The app is running in background: 3
    # The app is running in foreground: 4



# self.driver.execute_script("mobile: changePermissions", {
#                                   permissions: 'all',
#                                   appPackage: '',
#                                   action: 'allow',
# })
#  mobile: 


# deviceInfo::
# androidId
# manufacturer
# model
# brand
# apiVersion
# platformVersion
# carrierName
# realDisplaySize
# displayDensity
# networks
# locale
# timeZone
# bluetooth


# adb -t 31 shell monkey -p com.netflix.mediaclient -c android.intent.category.LAUNCHER 1
