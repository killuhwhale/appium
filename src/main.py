# from offerup.post import post_offer
# from offerup.crawl import crawl
from playstore.playstore import AppValidator
from time import sleep
# from utils.utils import android_des_caps
from typing import AnyStr, List, Dict
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import WebDriverException
from utils.parallel import MultiprocessTaskRunner
from utils.utils import (
    ARC_VERSIONS, CRASH_TYPE, PLAYSTORE_PACKAGE_NAME, PLAYSTORE_MAIN_ACT, TOP_500_APPS, 
    adb_connect, android_des_caps, check_crash, check_for_win_death, check_force_remove_record,
    find_transport_id, get_arc_version, get_cur_activty, get_start_time, open_app)


# Multiprocessing Runs

ips = [
    # '192.168.1.238:5555',
    '192.168.1.113:5555',
    # '710KPMZ0409387',  # Device connected via USB (Pixel 2)

]
runner = MultiprocessTaskRunner(ips, TOP_500_APPS[:1])
runner.run()

###################################
#   Single run
###################################

# ip = '710KPMZ0409387' # ARC-R
# ip = '192.168.1.238:5555' # ARC-R Helios, Failing on install step ##*#*#*#*#*#**#*##*
# ip = '192.168.1.113:5555' # ARC-P

# res = adb_connect(ip)
# transport_id = find_transport_id(ip)
# version = get_arc_version(transport_id)

# stop = ""
# test_txt = '''
# 12-28 17:43:22.474   153   958 I ActivityManager: START u0 {act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] flg=0x10200000 cmp=com.Psyonix.RL2D/com.epicgames.ue4.SplashActivity} from uid 2000
# 12-28 17:43:22.494   153   958 I ActivityManagerInjectorArc: notifyActivityAddedToTask: added to new task. activity=ActivityRecord{dc0b424 u0 com.Psyonix.RL2D/com.epicgames.ue4.SplashActivity t190}
# 12-28 17:43:22.497   153   958 I ActivityManagerInjectorArc: notifyActivityAddedToTask: added to new task. activity=ActivityRecord{dc0b424 u0 com.Psyonix.RL2D/com.epicgames.ue4.SplashActivity t190}
# 12-28 17:43:23.055  8171  8171 I chatty  : uid=10176(com.Psyonix.RL2D) expire 157 lines
# 12-28 17:43:23.056   153   243 I ActivityManager: Start proc 8171:com.Psyonix.RL2D/u0a176 for activity com.Psyonix.RL2D/com.epicgames.ue4.SplashActivity
# 12-28 17:43:23.173  8171  8192 I chatty  : uid=10176(com.Psyonix.RL2D) expire 8 lines
# 12-28 17:43:23.186  8171  8213 I chatty  : uid=10176(com.Psyonix.RL2D) expire 1 line
# 12-28 17:43:23.189  8171  8215 I chatty  : uid=10176(com.Psyonix.RL2D) expire 15 lines
# 12-28 17:43:23.199  8171  8219 I chatty  : uid=10176(com.Psyonix.RL2D) expire 22 lines
# 12-28 17:43:23.225  8171  8222 I chatty  : uid=10176(com.Psyonix.RL2D) expire 4 lines
# 12-28 17:43:23.229  8171  8223 I chatty  : uid=10176(com.Psyonix.RL2D) expire 3 lines
# 12-28 17:43:23.313   617   617 D ArcAppTaskTracker: Task created: 190 - ComponentInfo{com.Psyonix.RL2D/com.epicgames.ue4.SplashActivity} .
# 12-28 17:43:23.351   153  5488 I ActivityManager: START u0 {act=android.intent.action.MAIN flg=0x10000 cmp=com.Psyonix.RL2D/com.epicgames.ue4.GameActivity (has extras)} from uid 10176
# 12-28 17:43:23.416  8171  8227 I chatty  : uid=10176(com.Psyonix.RL2D) expire 4 lines
# 12-28 17:43:23.743  8171  8180 I chatty  : uid=10176(com.Psyonix.RL2D) expire 1 line
# 12-28 17:43:23.805  8171  8235 I chatty  : uid=10176(com.Psyonix.RL2D) expire 8 lines
# 12-28 17:43:24.086   153  5488 I ActivityManagerInjectorArc: Root activity removed from task: ActivityRecord{dc0b424 u0 com.Psyonix.RL2D/com.epicgames.ue4.SplashActivity t-1 f}
# 12-28 17:43:24.543  8171  8233 I chatty  : uid=10176(com.Psyonix.RL2D) expire 75 lines
# 12-28 17:43:25.000  8171  8291 I chatty  : uid=10176(com.Psyonix.RL2D) expire 2 lines
# 12-28 17:43:25.059   153   509 I WindowManager: WIN DEATH: Window{d3d2da1 u0 com.Psyonix.RL2D/com.epicgames.ue4.GameActivity}
# 12-28 17:43:25.060   153  5441 I ActivityManager: Process com.Psyonix.RL2D (pid 8171) has died: fore TOP 
# 12-28 17:43:25.063   153  4488 I WindowManager: WIN DEATH: Window{148a787 u0 com.Psyonix.RL2D/com.epicgames.ue4.GameActivity}
# 12-28 17:43:25.096   153  5441 W ActivityManager: Force removing ActivityRecord{a2dea97 u0 com.Psyonix.RL2D/com.epicgames.ue4.GameActivity t190}: app died, no saved state
# 12-28 17:43:25.101    16    28 W SurfaceFlinger: Attempting to destroy on removed layer: AppWindowToken{15e246d token=Token{ad11484 ActivityRecord{a2dea97 u0 com.Psyonix.RL2D/com.epicgames.ue4.GameActivity t190}}}#0
# 12-28 17:43:32.424  8297  8297 W Monkey  : args: [--pct-syskeys, 0, -p, com.Psyonix.RL2D, -c, android.intent.category.LAUNCHER, 1]
# 12-28 17:43:32.425  8297  8297 W Monkey  :  arg: "com.Psyonix.RL2D"
# 12-28 17:43:32.425  8297  8297 W Monkey  : data="com.Psyonix.RL2D"
# 12-28 17:43:32.459   153  4488 I ActivityManager: START u0 {act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] flg=0x10200000 cmp=com.Psyonix.RL2D/com.epicgames.ue4.SplashActivity} from uid 2000
# 12-28 17:43:32.466   153  4488 I ActivityManagerInjectorArc: notifyActivityAddedToTask: added to new task. activity=ActivityRecord{b939468 u0 com.Psyonix.RL2D/com.epicgames.ue4.SplashActivity t191}
# 12-28 17:43:32.525    16    16 D wayland-service: Creating app window for task_id 191 from package 'com.Psyonix.RL2D'
# 12-28 17:43:32.525    16    16 I wayland-service: Set task 191 orientation lock from package 'com.Psyonix.RL2D'
# 12-28 17:43:32.525    16    16 I wayland-service: Set task 191 window type 1from package 'com.Psyonix.RL2D
# 12-28 17:43:32.468   153  4488 I ActivityManagerInjectorArc: notifyActivityAddedToTask: added to new task. activity=ActivityRecord{b939468 u0 com.Psyonix.RL2D/com.epicgames.ue4.SplashActivity t191}
# 12-28 17:43:32.987  8343  8343 I chatty  : uid=10176(com.Psyonix.RL2D) expire 157 lines
# 12-28 17:43:32.999   153   243 I ActivityManager: Start proc 8343:com.Psyonix.RL2D/u0a176 for activity com.Psyonix.RL2D/com.epicgames.ue4.SplashActivity
# 12-28 17:43:33.055  8343  8363 I chatty  : uid=10176(com.Psyonix.RL2D) expire 2 lines
# 12-28 17:43:33.083  8343  8365 I chatty  : uid=10176(com.Psyonix.RL2D) expire 8 lines
# 12-28 17:43:33.099  8343  8377 I chatty  : uid=10176(com.Psyonix.RL2D) expire 1 line
# 12-28 17:43:33.100  8343  8379 I chatty  : uid=10176(com.Psyonix.RL2D) expire 15 lines
# 12-28 17:43:33.108  8343  8383 I chatty  : uid=10176(com.Psyonix.RL2D) expire 22 lines
# 12-28 17:43:33.113  8343  8386 I chatty  : uid=10176(com.Psyonix.RL2D) expire 4 lines
# 12-28 17:43:33.115  8343  8387 I chatty  : uid=10176(com.Psyonix.RL2D) expire 3 lines
# 12-28 17:43:33.122   617   617 D ArcAppTaskTracker: Task created: 191 - ComponentInfo{com.Psyonix.RL2D/com.epicgames.ue4.SplashActivity} .
# 12-28 17:43:33.142   153  4663 I ActivityManager: START u0 {act=android.intent.action.MAIN flg=0x10000 cmp=com.Psyonix.RL2D/com.epicgames.ue4.GameActivity (has extras)} from uid 10176
# 12-28 17:43:33.145  8343  8390 I chatty  : uid=10176(com.Psyonix.RL2D) expire 4 lines
# 12-28 17:43:33.506  8343  8348 I chatty  : uid=10176(com.Psyonix.RL2D) expire 1 line
# 12-28 17:43:33.564  8343  8408 I chatty  : uid=10176(com.Psyonix.RL2D) expire 8 lines
# 12-28 17:43:33.583    16    16 D SurfaceFlinger: duplicate layer name: changing com.Psyonix.RL2D/com.epicgames.ue4.GameActivity to com.Psyonix.RL2D/com.epicgames.ue4.GameActivity#1
# 12-28 17:43:33.770   153  4663 I ActivityManagerInjectorArc: Root activity removed from task: ActivityRecord{b939468 u0 com.Psyonix.RL2D/com.epicgames.ue4.SplashActivity t-1 f}
# 12-28 17:43:33.876    16   369 W SurfaceFlinger: Attempting to set client state on removed layer: Splash Screen com.Psyonix.RL2D#0
# 12-28 17:43:33.876    16   369 W SurfaceFlinger: Attempting to destroy on removed layer: Splash Screen com.Psyonix.RL2D#0
# 12-28 17:43:34.115  8343  8406 I chatty  : uid=10176(com.Psyonix.RL2D) expire 79 lines
# 12-28 17:43:36.730  8343  8420 I chatty  : uid=10176(com.Psyonix.RL2D) expire 1 line
# 12-28 17:43:36.731  8343  8474 I chatty  : uid=10176(com.Psyonix.RL2D) expire 3 lines
# 12-28 17:43:36.750  6437  6749 I Finsky  : [6173] gvo.c(2): getSessionStates for package: com.Psyonix.RL2D
# 12-28 17:43:36.759  8343  8355 I chatty  : uid=10176(com.Psyonix.RL2D) expire 1 line
# 12-28 17:43:37.594  8343  8469 I chatty  : uid=10176(com.Psyonix.RL2D) expire 15 lines
# 12-28 17:43:37.944  8343  8501 I chatty  : uid=10176(com.Psyonix.RL2D) expire 3 lines
# 12-28 17:43:43.648    16    69 D wayland-service: Removing task_id 191 from package 'com.Psyonix.RL2D'
# 12-28 17:43:44.384  8343  8407 I chatty  : uid=10176(com.Psyonix.RL2D) expire 2 lines
# 12-28 17:43:44.722   153   509 I WindowManager: WIN DEATH: Window{4a67a55 u0 com.Psyonix.RL2D/com.epicgames.ue4.GameActivity}
# 12-28 17:43:44.722   153   961 I ActivityManager: Process com.Psyonix.RL2D (pid 8343) has died: cch  CEM 
# 12-28 17:43:44.730    16    27 W SurfaceFlinger: Attempting to destroy on removed layer: AppWindowToken{429e361 token=Token{3d166c8 ActivityRecord{df6cb6b u0 com.Psyonix.RL2D/com.epicgames.ue4.GameActivity t191}}}#0
# 12-28 17:46:56.050  8530  8530 W Monkey  : args: [--pct-syskeys, 0, -p, com.Psyonix.RL2D, -c, android.intent.category.LAUNCHER, 1]
# 12-28 17:46:56.051  8530  8530 W Monkey  :  arg: "com.Psyonix.RL2D"
# 12-28 17:46:56.051  8530  8530 W Monkey  : data="com.Psyonix.RL2D"
# 12-28 17:46:56.116   153  5488 I ActivityManager: START u0 {act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] flg=0x10200000 cmp=com.Psyonix.RL2D/com.epicgames.ue4.SplashActivity} from uid 2000
# 12-28 17:46:56.122   153  5488 I ActivityManagerInjectorArc: notifyActivityAddedToTask: added to new task. activity=ActivityRecord{9399406 u0 com.Psyonix.RL2D/com.epicgames.ue4.SplashActivity t192}

# '''
# while stop != "q":
#     '''
#         adb -t 10 logcat | grep -i com.Psyonix.RL2D
#         12-28 17:48:37.233   153   235 I WindowManager: WIN DEATH: Window{913e5ce u0 com.Psyonix.RL2D/com.epicgames.ue4.GameActivity}
#         12-28 17:48:37.254   153  4857 W ActivityManager: Force removing ActivityRecord{f024fcc u0 com.Psyonix.RL2D/com.epicgames.ue4.GameActivity t195}: app died, no saved state

#     '''
#     start_time = get_start_time()
#     open_app(TOP_500_APPS[0][1] ,str(transport_id), version)
#     sleep(5)
#     crash_type, crashed_act = check_crash('com.Psyonix.RL2D', start_time, transport_id)
#     if(not crash_type == CRASH_TYPE.SUCCESS):
#         print(f"failed act: {crashed_act}, {crash_type.value}")
#     else:
#         print("App didnt fail!")

#     stop = input("stop")


# # adb logcat -v time -t 22:28:35
# driver = webdriver.Remote(
#     "http://localhost:4723/wd/hub",
#     android_des_caps(
#         ip,
#         PLAYSTORE_PACKAGE_NAME,
#         PLAYSTORE_MAIN_ACT
#     )
# )
# driver.implicitly_wait(5)
# driver.wait_activity(PLAYSTORE_MAIN_ACT, 5)

# validator = AppValidator(driver, TOP_500_APPS[:5], transport_id, version)
# # validator.uninstall_multiple()
# validator.run()
# validator.report.print_report()
# driver.quit()













# Old Test code, still want...
# categories = {
#     'cell phone': 0,
#     'computer accessories': 1,
# }
# cooler = {
#     'title': "AIO 240mm CPU liquid cooler",
#     'desc': "TISHRIC Water Cooler CPU Fan 120 240 360mm RGB Cooling Fan Heatsink Intel LGA 2011/1151/AM3+/AMD AM4 Processor Cooler Radiator",
#     'price': "70",
#     'folder': 'cooler1',
#     'category': categories['cell phone'],
# }

# rack = {
#     'title': "Weightlifting rack and bench",
#     'desc': "ER KANG Multi-Functional Barbell Rack, 800 LBS Capacity Fitness Adjustable Power Cage Dip Stand Squat Power Rack for Home Gym, Weight Lifting, Bench OG price $235 + $ 90 ",
#     'price': "250",
#     'folder': 'rack',
#     'category': categories['computer accessories'],
# }


# post_offer(
#     driver=driver,
#     **rack
# )


# post_offer(
#     driver=driver,
#     title="Cooler",
#     desc='da coldest',
#     price='75',

# )

# crawl(driver)

