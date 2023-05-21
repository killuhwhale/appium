Example Output

<img src="https://raw.githubusercontent.com/killuhwhale/appium/main/src/images/readme/demo_output.png?sanitize=true&raw=true" />
<video src="https://drive.google.com/open?id=1kztEqXsqcLiEa24NN3vr3_ddeH0D0re4&authuser=0&usp=drive_link" />



# Deployment
## Login with AppVal002 to provide ADC to device that is running tests in order to upload to GCPBuckets
    gcloud auth application-default login



Prep work for Chromebook:
- DUT
    - Install Accounts for testing.
    - Turn on ADB
    - Connect Host and DUT to accept permission on DUT.

- Host device
    - Setup environment
        - bash ins_and_stu.sh
        - bash setup.sh (run twice if npm is not already installed.)
    - Add Files to Home Dir
        - app_list.txt place in home dir of host machine that contains apps to test.
    - Add Files to project
        - .env file in src/ w/ FIREBASE_HOST_POST_ENDPOINT_SECRET
    - Run Program
        python3 main.py -i 192.168.1.125:5555 192.168.1.113:5555       # Single run


# What we can do
1. 1 Host device -> 15 dut
    - ADB by default has 15 device connection limit
        - Ovverride with env variable: ADB_LOCAL_TRANSPORT_MAX_PORT
                static void adb_local_transport_max_port_env_override() {
                    const char* env_max_s = getenv("ADB_LOCAL_TRANSPORT_MAX_PORT");
                    ....
                }
    - min 15Gb of disk space
2. Supports ARC-P and ARC-R
    - improving model to work across varying screen sizes
3. Discover and Install Apps from Playstore
    - Check app's current name in Playstore (web)
    - Check if app is not avilable in our region
4. Can install and detect PWAs from Playstore
    - cannot interact with PWAs.
5. Can Detect if an app is a game.
5. Open app and detect crashing upon opening.
6. Attempt login using Object Detection via YOLOv8
7. Detect if app was logged in
    - if we are able to send username/ password or click on Google/ Facebook sign in without subsequent crash.
8. Log reports to file.
    - invalid apps, failed apps, passed apps, stats of apps, summary
9. Updates misnamed apps in app list
10. History report for each app w/ screenshots at ea step.
    - Includes:
        - App Install success/ failure
        - App Launch success/ failure
        - App Login success/ failure
        - App Errors
11. Summary report of all apps from each device.
12. Detects 3 types of login methods and attempts to login to each: Google, Facebook, Email

# What we need to do but cant yet
1. Detect if an app is O4C


# Reporting

1. Passed
2. Failed
    - Invalid/ bad app - No longer on playstore
    - Misnamed apps - Updated list
    - Failed apps
        - Not installed
        - Crashed



# Files in user home dir
1. App list.txt
    - List of apps to test
2. Bad app list.txt
    - List of apps no longer available
    - Removed from app list and placed into bad app list
    - Currently happens at the end of a run.
        - This can be done live

3 & 4 Will Have: device info, app info, app status info w/ reasons for failure (if app failed)
3. Failed app.tsv (DATA SRC)
    - Added during the run to prevent data loss during long run
4. Passed apps.tsv (DATA SRC)
    - Added during the run to prevent data loss during long run

5. Report
    - Human readable print after a full run.
    - More difficult to gather in memory, not really worth the effort if we end up building out a dashboard w/ web UI.
    - Focus on #4, 5 that is essentially our data source whereas 1 and 2 keep our testing list updated while still trakcing invalid apps.


# Django webserver - runs local on host machine
    ## websocketapp
    - Establish wss connection to GCP server






# TODOs


    - Add Playstore checks from app_launcher to App_validator to also check when we fail to click app_icon in app_installer....


    - Free Fire failed to detect Facebook (most likely download took to long)
        - Try to detect Free Fire download via adb
    - Messenger Kids - Failed to click/recognize 'Authorize device" as continue btn to finish logging in.
        - Scraped, need to add to dataset.

    - Facebook takes like 43 seconds to open when trying to login with email/password which made the login attempts run out while wainting for FB....
        - Check to see if we can see any loading activity from ADB.

     - Explore  OCR on bounding boxes for continue to see what button we have.
        - We can then decided which order or what not to click based on the text of the button.



    Raw Image sizes from device SS:
        - W x H
        - 2400 x 1600 Eve, Caroline
        - 1920 x 1080 Helios
        - 2700 x 1800 CoachZ
        - 2160, 1440 (Ethan eve? screenshots straight from device)


        ____________________
        ________________|  |
        _____________|  |  |
                     |  |  |
        HElios    -->|  |  |
        Eve       -->-->|  |
        CoachZ    -->-->-->|



    Size of report:
        ~ 5kB per app - 1000 apps -> 5mB
        1 item: 7.89 KB
        Size of validation report dict (5): 27.77 KB
        Size of validation report dict (6): 29.59 KB
        Size of validation report dict (7): 32.03 KB


 Make Money: Play & Earn Cash   us.current.android   PASSED   - [eve_192.168.1.125:5555]
 AppData(name='us.current.android', versionCode='647', versionName='1.177.1', compileSdkVersion='33', compileSdkVersionCodename='13', platformBuildVersionName='', is_pwa=False, is_game=False)
         Final status:   Logged in.
         Logged in with: Google, Email
         Detected log in methods: Google, Email
         App install successfull.
                 Img: /home/killuh/ws_p38/appium/src/images/history/192.168.1.125:5555/us.current.android/0.png
         Google Auth sign-in
                 Img: /home/killuh/ws_p38/appium/src/images/history/192.168.1.125:5555/us.current.android/1.png
         Email/ password sign-in
                 Img: /home/killuh/ws_p38/appium/src/images/history/192.168.1.125:5555/us.current.android/2.png












    Future TODOs:

     - Reporting that apps not logged in when in fact, we did log in and have the SS to prove.
        - Small problem, only affect facebook apps like Messenger.
            - we should be able to find a small workout around.
                - Hard code behavior for com.facebook.* packages.


    - Create a few sample app APKs that will do a specific crash/ throw ANR.
        - I cant seem to figure out how to reproduce:
            - WIN_DEATH = "Win Death"
            - FORCE_RM_ACT_RECORD = "Force removed ActivityRecord"
            - FDEBUG_CRASH = "F DEBUG crash"

        - Able to create an app that reproduces an ANR...
            - Minimally helpful.


    - Detect AMAC-e (determine if app is O4C) -> impossible feat so far unless building test image.
        - AMAC-E overlays will not actually interfere with our process.
        - When sending comands via ADB, it essentially ignores those windows/ overlays.

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

