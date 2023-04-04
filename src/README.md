Example Output

<img src="https://raw.githubusercontent.com/killuhwhale/appium/main/src/images/readme/demo_output.png?sanitize=true&raw=true" />
<video src="https://drive.google.com/open?id=1kztEqXsqcLiEa24NN3vr3_ddeH0D0re4&authuser=0&usp=drive_link" />

LINE TO CHANGE IN yolov8 engine/model.py

overrides['save'] = kwargs.get('save', False)  # not save files by default

Prep work for Chromebook:
- DUT
    - Install Accounts for testing.
    - Turn on ADB
    - Connect Host and DUT to accept permission on DUT.

- Host device
    - Setup environment
        - bash ins_and_stu.sh
        - bash setup.sh (run twice if npm is not already installed.)
    - python3 main.py [ips]
    - python3 main.py 192.168.1.113:5555 192.168.1.238:5555 192.168.1.248:5555


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
6. Attempt login using Object Detection via YOLOv5
7. Detect if app was logged in
    - if we are able to send username/ password or click on Google/ Facebook sign in without subsequent crash.
8. Log reports to file.
    - misnamed apps, invalid apps and failed apps
9. Update misnamed apps
10. History report for each app w/ screenshots at ea step.
11. Summary report of all apps from each device.

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



# TODOs

    - Write utility class to install an apk
        - We should be able to skip the installation step and install apk directly and continue like normal
        - Create/ Curate apks that will fails to demo/ test our process is working correctly for the errors we are trying to catch.

    - App demo list issues...
        - Messenger
            - Smart lock appear first... doest pick an account..
                - Helios
        - Duolingo
            - Fails clicked on password? Coachz

        - Messenger Kids
            - Confirm button isnt detected....

        - Free Fire and see if is_download in progress...
            - Took too long to load

        - Roblox
            - Took too long Eve
            - Didnt find Login field CoachZ

        - Wish
            - Failed, continue with accounts appear early..  Helios


    - Detection: Instead of saving as file and reading as file
        - It already gets the file as b64 in memory, lets just use that and pass that into the detector instead of by file.
            - Should be ,much quicker
            - Need to find out what types of sources we can use....
                - ss as b64 -> png -> to file, read file -> .png -> detector

    - Record which log in method was used or to use, GAuth, FBAuth, email/pass
        - Figure out how to attempt multiple logins on each app.
            - After Installed, perform a cycle check until we find login field or GAuth or FBAuth
                - Depending on what we find, we will attempt those methods.
                - So we start with a general search with only Continue buttons until we find a SS w/ a login method.
                    - If multiple methods, cycle through ea method
                    - If one method just try that one.
                - Then we can report which methods were tried and their status

    - Strategy when we have two continue buttons and one is disabled but has the higher probability
        - we should try to click all of them unless something happens?
            - Make it try more continue buttons before takinga new screenshot...??
            - Gacha life
                - Cancel Agree Continue buttons are conflicting.

    - Improve model
        -1. Explore Age verification
            - input age or slider
            - we are detecting "2" for num pads
            - WE WILL NEED TO detect slider age bars.
                - click in center of view
            - Empty form fields to type age will probably be the trickiest...


        NOTE:
        *** Update to YOLOv7? slight increase in accuracy ~3% (from what I've read)
        *** Most likely will need to scrape same image set from multiple devices w/ varying screen sizes.




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

