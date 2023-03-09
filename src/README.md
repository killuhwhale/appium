Example Output

<img src="https://raw.githubusercontent.com/killuhwhale/appium/main/src/images/readme/demo_output.png?sanitize=true&raw=true" />
<video src="https://drive.google.com/open?id=1kztEqXsqcLiEa24NN3vr3_ddeH0D0re4&authuser=0&usp=drive_link" />


Prep work for Chromebook:
- DUT
    - Install Accounts for testing.
    - Turn on ADB
    - Connect Host and DUT to accept permission on DUT.

- Host device
    - Setup environment
        - bash ins_and_stu.sh
        - bash setup.sh (run twice if npm was not already installed.)
    - python3 main.py [ips]
    - python3 main.py python3 main.py 192.168.1.113:5555 192.168.1.238:5555 192.168.1.248:5555


# What we can do
1. 1 Host device -> 15 dut
    - ADB by default has 15 device connection limit
        - Ovverride with env variable: ADB_LOCAL_TRANSPORT_MAX_PORT
                static void adb_local_transport_max_port_env_override() {
                    const char* env_max_s = getenv("ADB_LOCAL_TRANSPORT_MAX_PORT");
                    ....
                }
2. Supports ARC-P and ARC-R
    - improving model to work across varying screen sizes
3. Discover and Install Apps from Playstore
    - Check app's current name in Playstore (web)
    - Check if app is not avilable in our region
4. Can install and detect PWAs from Playstore
    - cannot interact with PWAs.
5. Can Detect if an app is a game.
5. Open app and detect crashing upon opening.
6. History report for each app w/ images at ea step.
7. Summary report of all apps.

# What we need to do but cant yet
1. Detect app if an app is O4C



# Major TODOs

    # install button - def install_app_UI()
        - Need to verify if stable build is different than other builds
        - Seems two methods work depending on BUILD.
                - on stable we use ACCESSIBILITY ID query
                - on non stable we use button.text == install query

    # Random errors with Appium/ UIAutomator
        - Might need to explore checking UIAutomator server?
            - UiAutomator2 server because the instrumentation process is not running (probably crashed)

        192.168.1.238:5555 -  Error taking SS:  Message: An unknown server-side error occurred while processing the command. Original error: 'GET /screenshot' cannot be proxied to UiAutomator2 server because the instrumentation process is not running (probably crashed). Check the server log and/or the logcat output for more details
        Stacktrace:
        UnknownError: An unknown server-side error occurred while processing the command. Original error: 'GET /screenshot' cannot be proxied to UiAutomator2 server because the instrumentation process is not running (probably crashed). Check the server log and/or the logcat output for more details
            at UIA2Proxy.command (/home/killuh/.nvm/versions/node/v18.7.0/lib/node_modules/appium/node_modules/appium-base-driver/lib/jsonwp-proxy/proxy.js:274:13)
            at processTicksAndRejections (node:internal/process/task_queues:95:5)
            at AndroidUiautomator2Driver.commands.getScreenshot (/home/killuh/.nvm/versions/node/v18.7.0/lib/node_modules/appium/node_modules/appium-uiautomator2-driver/lib/commands/screenshot.js:14:10)
        192.168.1.238:5555 -  Error taking SS:  /home/killuh/ws_p38/appium/src

    - Create a file to store the apps list
        - we encountering an app that we cant find on the playstore, we check the web for region or name issue
            - Region issue, we move to another file/ list and remove from current list
            - Name issue, simply update the name in the OG file.


    - Improve model
        *** Update to YOLOv7? slight increase in accuracy ~3% (from what I've read)

        -1. Explore Age verification
            - input age or slider
            - we are detecting "2" for num pads
            - WE WILL NEED TO detect slider age bars.
                - click in center of view
            - Empty form fields to type age will probably be the trickiest...

        -3. Most likely will need to scrape same image set from multiple devices w/ varying screen sizes.


    Future TODOs
    - Create a few sample app APKs that will do a specific crash/ throw ANR.
        - I cant seem to figure out how to reproduce:
            - WIN_DEATH = "Win Death"
            - FORCE_RM_ACT_RECORD = "Force removed ActivityRecord"
            - FDEBUG_CRASH = "F DEBUG crash"

        - Able to create an app that reproduces an ANR...
            - Minimally helpful.


    - Detect AMAC-e (determine if app is O4C) -> impossible feat so far unless building test image.
        - AMAC-E overlays will not actually interfere with our process.
        - When sending comands via ADB, it essentially ignore those windows/ overlays.



Bugs:



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

