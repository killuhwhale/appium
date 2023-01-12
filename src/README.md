Example Output

<img src="https://raw.githubusercontent.com/killuhwhale/appium/main/src/images/readme/demo_output.png?sanitize=true&raw=true" />
<video src="https://drive.google.com/open?id=1kztEqXsqcLiEa24NN3vr3_ddeH0D0re4&authuser=0&usp=drive_link" />


Prep work for Chromebook:
- DUT
    - Install Accounts for testing.
- Host device
    - Setup environment
        - bash ins_and_stu.sh
        - bash setup.sh
    - python3 main.py [ips]
    - python3 main.py python3 main.py 192.168.1.113:5555 192.168.1.238:5555 192.168.1.248:5555


# Need to test on Chromebook
Need to understand if devices will have preinstalled accounts
    - Need accounts like testminnie001@gmail.com logged into device


Improve model
App version
Manifest DL
Identify Android vs PWA & AMAC-e
Games vs App - Surface View check
Log each step of testing instead of just reporting failures.


Problems:


    Credentails:
        - Make a small toool to easily seach for creds that arent filled in.
        - Allow testers to search quickly
            - If a tester is testing an app, they shoudl search the tool
                - If they are testing an app and its on the list of unfilled creds
                    - Allow tester to add creds


    - Figure out a strategy/ design for loggin into apps w/ a variety of accounts.

    Store Packages with accounts.

    APP_CREDS = {
        package_name: {
            strat: ['inputFields' | 'GoogleAuthText' | 'GoogleAuthOCR' | "FBAuthText" | "FBAuthOCR" ],
            accounts: [['email/username/phonenumber', 'password'], [], ...]
            auth_accounts_text: ['email text'] # This should work for Google, they show Rows with Profile Icon & Email, not exactly sure for FaceBook.
            auth_accounts_OCR: [ '/path/to/account_icon.png']
        },
        com.roblox: {
            strat: ['inputFields'],
            accounts: [['testminnie001@gmail.com', 'testminnie123'],]
            auth_accounts_text: []
            auth_accounts_OCR: []
        },
        com.netflix: {
            strat: ['Google Auth text'],
            accounts: []
            auth_accounts_text: ['testminnie001@gmail.com']
            auth_accounts_OCR: []
        }
        com.anothaone: {
            strat: ['Google Auth OCR'],
            accounts: []
            auth_accounts_text: []
            auth_accounts_OCR: ['/path/to/profile-icon.png']
        }
    }


    # For each app we will know the stratgeyt to use.
    We can then build multiple handle_login() flows to handle each strategy.
        - We already need to build something to login, so we already need to map accounts to apps for login.
            - No way around that
            -
        - For each app we decide to user input fields or SSO Auth from Google or FaceBook

        - For input field login:
            - We need a set of email/password strings to use for each app
        - For SSO:
            - In order to click the right account
            - We need a string or an icon to search the screen for.
                - String: email to use OCR to find location on screen.
                - Icon: image of account icon to find.








    - com.google.android.contacts
        - wont uninstall
            Makes the beginning uninstall check take a long time


TODO:

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

