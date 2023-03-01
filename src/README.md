Example Output

<img src="https://raw.githubusercontent.com/killuhwhale/appium/main/src/images/readme/demo_output.png?sanitize=true&raw=true" />
<video src="https://drive.google.com/open?id=1kztEqXsqcLiEa24NN3vr3_ddeH0D0re4&authuser=0&usp=drive_link" />


Prep work for Chromebook:
- DUT
    - Install Accounts for testing.
    - Turn on ADB
- Host device
    - Setup environment
        - bash ins_and_stu.sh
        - bash setup.sh
    - python3 main.py [ips]
    - python3 main.py python3 main.py 192.168.1.113:5555 192.168.1.238:5555 192.168.1.248:5555



# Major TODOs
    - Label Facebook Auth in Dataset
        - Also, possibly create a flow to login to facebook app before tests so that we can use it for auth in the rest of the apps...

    - Google Auth account selection
        - scrape images for Google Auth Selection
            - Find a profile pic that will be used w/ our test accounts.

    - Detect AMAC-e (determine if app is O4C) -> impossible feat so far unless building test image.
        - AMAC-E overlays will not actually interfere with our process.
        - When sending comands via ADB, it essentially ignore those windows/ overlays.

    - Improve model
        - Most likely will need to scrape same image set from multiple devices w/ varying screen sizes.
        - Detection that works on Coach-Z does not work as well on HElios
            - Different screen sizes.
            - Resizing doesnt seem to help in this case.
                - Try resizing to CoachZ size? instead of resizing to 640x640

            - Resizing to CoachZ kinda work but Roblox:
                - Didnt recognize Login field
                    - It usually recongizes this so this solution wont work.

            - Might need to really scrape from multiple devices....

               | Reported Display size | Appears Size |
            - CoachZ (2160 1440 native 1200 x 800 @ 100%) 1.5
            - Helios (1920 1080 native   ?  x  ?  @ 100%) 1.78
            - Eve    (2400 1600 native   ?  x  ?  @ 100%) 1.5
            The reported display size is the size of the image.

            - Ultimately, we wont need to resize if our dataset contains the sizes we need....
                - or we resize everything to 640x640
                - Since in our training, we resize the training img to 640^2


Bugs:

    - Pulling APK:  com.nordvpn.android /home/killuh/ws_p38/appium/src/apks/com.nordvpn.android
        Error in main RUN:  Command '('/home/killuh/Android/Sdk/build-tools/31.0.0/aapt', 'dump', 'badging', '/home/killuh/ws_p38/appium/src/apks/com.nordvpn.android/base.apk')' returned non-zero exit status 1.
    - Handle Login
        - Some apps requrie :
            - Dropdown Birthday Selections
            - Age number slider

- ['Summoners War', 'com.com2us.smon.normal.freefull.google.kr.android.common'], # Faisl to download extra data but
        doesnt crash app


# NOTES

-  adb exec-out uiautomator dump /dev/tty
        - Dumps view heirarchy

# https://github.com/appium/appium-uiautomator2-driver#driverserver
#   - appium:skipServerInstallation => Improve startup speed if we know UIAutomator is already installed...


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

