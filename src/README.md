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



 - Improve model
 - Log each step of testing instead of just reporting failures - to do
    - Figure out a loggin system.
    - Alredy have a failure logging system. Can extend it to support a detailed desc of what ahppens with each app.
 - Identify Android vs PWA & AMAC-e
    - near impossible  or what?



# NOTES

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

