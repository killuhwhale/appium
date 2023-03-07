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

    - Create a few sample app APKs that will do a specific crash/ throw ANR.
        -

    - Explore #  Error pulling APK for Google Dopcs....
        - utils::AppInfo.__download_manifest
            #  Error pulling APK for Google Dopcs....
            # Creating dir:  /home/killuh/ws_p38/appium/src/apks/com.google.android.apps.docs.editors.docs
            # File exists  False
            # Found apk path: /data/app/~~l6As1JaBbzfOUaRahSBNOw==/com.google.android.apps.docs.editors.docs-O_-EXzQII1SOs34VUrEYKw==/base.apk
            # Pulling APK:  com.google.android.apps.docs.editors.docs /home/killuh/ws_p38/appium/src/apks/com.google.android.apps.docs.editors.docs
            # Error in main RUN:  Command '('/home/killuh/Android/Sdk/build-tools/31.0.0/aapt', 'dump', 'badging', '/home/killuh/ws_p38/appium/src/apks/com.google.android.apps.docs.editors.docs/base.apk')' returned non-zero exit status 1.
            # Gettign APK  com.gameloft.android.ANMP.GloftA8HM
            # Create dir if not exist /home/killuh/ws_p38/appium/src/apks/com.gameloft.android.ANMP.GloftA8HM
            # Error in main RUN:  Command '('/home/killuh/Android/Sdk/build-tools/31.0.0/aapt', 'dump', 'badging', '/home/killuh/ws_p38/appium/src/apks/com.gameloft.android.ANMP.GloftA8HM/base.apk')' returned non-zero exit status 1.
            #  Found apk path: /data/app/~~DkRw85cQTyThUz1sT_nbWw==/com.gameloft.android.ANMP.GloftA9HM-gbtLHWdEcWsgVYbHDfieHQ==/base.apk
            # Pulling APK:  com.gameloft.android.ANMP.GloftA9HM /home/killuh/ws_p38/appium/src/apks/com.gameloft.android.ANMP.GloftA9HM
            # Error in main RUN:  Command '('/home/killuh/Android/Sdk/build-tools/31.0.0/aapt', 'dump', 'badging', '/home/killuh/ws_p38/appium/src/apks/com.gameloft.android.ANMP.GloftA9HM/base.apk')' returned non-zero exit status 1.


    -  Searhing for app_icon with content desc:  new UiSelector().descriptionMatches(".*Transformers:.*");
        - Make case insensitve

    - Add feature - Useful for maintaining the project long term...
        - Get updated App name from Google play via package name if we fail to find it....
            - Sometimes the appname in the list is outdated

    - Explore Age verification
        - Possiblyy search through views to find "Age" related views...

    - Add a check for:
        -1. "No Thanks" when playstore first opens. This will block Search bar.
            - Only happens on first start of playstore....


    - Add a process to download and login to Facebook ARC++
        - so that other apps can use it to login, instead of using ChromeOS Chrome browser.
        - Close facebook after each app run, it will open multiple app instances for login....
            - Actually if we log in with facebook, this should automatically close. But if we dont finished loggin in these remain.
                - Might be good to just do this in case of log in failures or crashes???


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

          | Reported Display size(ADB) | Appears Size(Chrome Settings) |
            - CoachZ (2160 1440 native 1200 x 800 @ 100%) 1.5
            - Helios (1920 1080 native   ?  x  ?  @ 100%) 1.78
            - Eve    (2400 1600 native   ?  x  ?  @ 100%) 1.5
            The reported display size is the size of the image.

            - Ultimately, we wont need to resize if our dataset contains the sizes we need....
                - or we resize everything to 640x640
                - Since in our training, we resize the training img to 640^2


Bugs:




    - Hempire - ca.lbcstudios.hempire - stalled during loading
        03-03 18:34:58.473  8357  8469 E Unity   : AndroidJavaException: java.lang.UnsatisfiedLinkError: dlopen failed: library "libfmod.so" not found
        03-03 18:34:58.473  8357  8469 E Unity   : java.lang.UnsatisfiedLinkError: dlopen failed: library "libfmod.so" not found
        03-03 18:34:58.473  8357  8469 E Unity   : 	at java.lang.Runtime.loadLibrary0(Runtime.java:1087)


    TODO() log check for F DEBUG...
    03-03 14:36:13.059 19417 19417 F DEBUG   : *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***
    03-03 14:36:13.060 19417 19417 F DEBUG   : Build fingerprint: 'google/hatch/hatch_cheets:11/R112-15357.0.0/9629516:user/release-keys'
    03-03 14:36:13.060 19417 19417 F DEBUG   : Revision: '0'
    03-03 14:36:13.060 19417 19417 F DEBUG   : ABI: 'x86_64'
    03-03 14:36:13.060 19417 19417 F DEBUG   : Timestamp: 2023-03-03 14:36:13-0800
    03-03 14:36:13.060 19417 19417 F DEBUG   : pid: 19381, tid: 19381, name: lay.KingsCastle  >>> com.PepiPlay.KingsCastle <<<
    03-03 14:36:13.060 19417 19417 F DEBUG   : uid: 10272
    03-03 14:36:13.060 19417 19417 F DEBUG   : signal 11 (SIGSEGV), code 1 (SEGV_MAPERR), fault addr 0x7abbb8ba5000
    03-03 14:36:13.060 19417 19417 F DEBUG   :     rax 0000000000000700  rbx 00000000ffffe088  rcx 00007abb70658a98  rdx 00007abbb66f5464
    03-03 14:36:13.060 19417 19417 F DEBUG   :     r8  00007abbb66f5464  r9  00007abbb66dac40  r10 000000000001b271  r11 000000000001b26d
    03-03 14:36:13.060 19417 19417 F DEBUG   :     r12 000000000001b269  r13 000000000000595f  r14 0000000000000000  r15 00000100000001b3
    03-03 14:36:13.060 19417 19417 F DEBUG   :     rdi 00000000024afb9c  rsi 14b33503725a22c8
    03-03 14:36:13.060 19417 19417 F DEBUG   :     rbp 00007abb70a0c000  rsp 00007abb706588d0  rip 000000000db404e6
    03-03 14:36:13.083 19417 19417 F DEBUG   : backtrace:
    03-03 14:36:13.083 19417 19417 F DEBUG   :       #00 pc 00000000007e04e6  [anon:Mem_0x20000000]


    - App stalls during download, its broken => com.miHoYo.bh3global && com.funplus.familyfarm' -> The bug report logs below are constantly shown... not sure if its related. Test on non-helios device.
        03-01 17:03:27.045   423   516 W ArcProcessService: Failed to reclaim page by MGLRU
        03-01 17:03:27.045   423   516 W ArcProcessService: java.io.FileNotFoundException: /sys/kernel/mm/lru_gen/admin: open failed: ENOENT (No such file or directory)
        03-01 17:03:27.045   423   516 W ArcProcessService: 	at libcore.io.IoBridge.open(IoBridge.java:492)
        03-01 17:03:27.045   423   516 W ArcProcessService: 	at java.io.FileInputStream.<init>(FileInputStream.java:160)
        03-01 17:03:27.045   423   516 W ArcProcessService: 	at java.io.FileInputStream.<init>(FileInputStream.java:115)
        03-01 17:03:27.045   423   516 W ArcProcessService: 	at java.io.FileReader.<init>(FileReader.java:58)
        03-01 17:03:27.045   423   516 W ArcProcessService: 	at com.android.server.arc.process.ArcProcessService$Mglru.readTotalBytes(Unknown Source:16)
        03-01 17:03:27.045   423   516 W ArcProcessService: 	at com.android.server.arc.process.ArcProcessService.applyHostMemoryPressure(Unknown Source:116)
        03-01 17:03:27.045   423   516 W ArcProcessService: 	at org.chromium.arc.mojom.ProcessInstance_Internal$Stub.acceptWithResponder(SourceFile:8)
        03-01 17:03:27.045   423   516 W ArcProcessService: 	at org.chromium.mojo.bindings.RouterImpl.access$000(SourceFile:5)
        03-01 17:03:27.045   423   516 W ArcProcessService: 	at org.chromium.mojo.bindings.RouterImpl$HandleIncomingMessageThunk.accept(SourceFile:1)
        03-01 17:03:27.045   423   516 W ArcProcessService: 	at org.chromium.mojo.bindings.Connector.readAndDispatchMessage(SourceFile:7)
        03-01 17:03:27.045   423   516 W ArcProcessService: 	at org.chromium.mojo.bindings.Connector.access$100(SourceFile:2)
        03-01 17:03:27.045   423   516 W ArcProcessService: 	at org.chromium.mojo.bindings.Connector$WatcherCallback.onResult(SourceFile:1)
        03-01 17:03:27.045   423   516 W ArcProcessService: 	at org.chromium.mojo.system.impl.WatcherImpl.onHandleReady(SourceFile:1)
        03-01 17:03:27.045   423   516 W ArcProcessService: Caused by: android.system.ErrnoException: open failed: ENOENT (No such file or directory)

        03-02 16:07:22.210   423   516 W ArcProcessService: Failed to reclaim page by MGLRU
        03-02 16:07:22.210   423   516 W ArcProcessService: java.io.FileNotFoundException: /sys/kernel/mm/lru_gen/admin: open failed: ENOENT (No such file or directory)
        03-02 16:07:22.210   423   516 W ArcProcessService: 	at libcore.io.IoBridge.open(IoBridge.java:492)
        03-02 16:07:22.210   423   516 W ArcProcessService: 	at java.io.FileInputStream.<init>(FileInputStream.java:160)
        03-02 16:07:22.210   423   516 W ArcProcessService: 	at java.io.FileInputStream.<init>(FileInputStream.java:115)
        03-02 16:07:22.210   423   516 W ArcProcessService: 	at java.io.FileReader.<init>(FileReader.java:58)
        03-02 16:07:22.210   423   516 W ArcProcessService: 	at com.android.server.arc.process.ArcProcessService$Mglru.readTotalBytes(Unknown Source:16)
        03-02 16:07:22.210   423   516 W ArcProcessService: 	at com.android.server.arc.process.ArcProcessService.applyHostMemoryPressure(Unknown Source:116)
        03-02 16:07:22.210   423   516 W ArcProcessService: 	at org.chromium.arc.mojom.ProcessInstance_Internal$Stub.acceptWithResponder(SourceFile:8)
        03-02 16:07:22.210   423   516 W ArcProcessService: 	at org.chromium.mojo.bindings.RouterImpl.access$000(SourceFile:5)
        03-02 16:07:22.210   423   516 W ArcProcessService: 	at org.chromium.mojo.bindings.RouterImpl$HandleIncomingMessageThunk.accept(SourceFile:1)
        03-02 16:07:22.210   423   516 W ArcProcessService: 	at org.chromium.mojo.bindings.Connector.readAndDispatchMessage(SourceFile:7)
        03-02 16:07:22.210   423   516 W ArcProcessService: 	at org.chromium.mojo.bindings.Connector.access$100(SourceFile:2)
        03-02 16:07:22.210   423   516 W ArcProcessService: 	at org.chromium.mojo.bindings.Connector$WatcherCallback.onResult(SourceFile:1)
        03-02 16:07:22.210   423   516 W ArcProcessService: 	at org.chromium.mojo.system.impl.WatcherImpl.onHandleReady(SourceFile:1)
        03-02 16:07:22.210   423   516 W ArcProcessService: Caused by: android.system.ErrnoException: open failed: ENOENT (No such file or directory)
        03-02 16:07:22.210   423   516 W ArcProcessService: 	at libcore.io.Linux.open(Native Method)
        03-02 16:07:22.210   423   516 W ArcProcessService: 	at libcore.io.ForwardingOs.open(ForwardingOs.java:166)
        03-02 16:07:22.210   423   516 W ArcProcessService: 	at libcore.io.BlockGuardOs.open(BlockGuardOs.java:254)
        03-02 16:07:22.210   423   516 W ArcProcessService: 	at libcore.io.IoBridge.open(IoBridge.java:478)
        03-02 16:07:22.210   423   516 W ArcProcessService: 	... 12 more



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

