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