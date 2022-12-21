Example Output

<img src="https://raw.githubusercontent.com/killuhwhale/appium/main/src/images/readme/playstore_output.png?sanitize=true&raw=true" />
<video src="https://raw.githubusercontent.com/killuhwhale/appium/main/src/images/readme/DEMO_APPIUM.MOV?sanitize=true&raw=true" />


# Need to test on Chromebook
Need to understand if devices will have preinstalled accounts
- Google Drive
- What does it look like on fresh install


Problems:

Appium can open an app and wait for an activity to load.
- However, we need to start a driver specifically for this and that is expensive (time wise)
- Also this would most likely separate discovery/ install from open and login.
    - THis is because we would start multiple drivers while needing to maintain the PlayStore driver
        - Again switching driver is expensive


com.google.android.contacts
- wont uninstall
    Makes the beginning uninstall check take a long time


TODO:

- Do a check at URL w/ package name
    - https://play.google.com/store/apps/details?id=com.watched.play
    - TO see if the package is even valid. 

- Detect 'bad' chars -> ó
    - Adb shell struggles to send these.
    - Need to find a solution
- Detect Platstore in Foreground before each app search/install loop
    -   Someitmes playstore crashes or isnt in the foreground and this will affect the loop
        - We should check and retore the playstore, at least once, at the beginning of the loop
            - Depedning on how fast this check is, we can check befre each step during the search/install phase.

- Find a reliable way to wait for current activity to be loaded when opening an app...
    - Games sometimes take a while to load/ download extra data

-  Create architecture to create multiple Drivers and start a job for each one. 
    - Currently, in main.py, we are just creating one driver.



Features/ Optimizations:

- Get size of an app to anticipate download time