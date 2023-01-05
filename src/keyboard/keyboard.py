import base64
import os
import subprocess
import __main__



ROOT_PATH = os.path.realpath(__main__.__file__).split("/")[1:-1]
ROOT_PATH = '/'.join(ROOT_PATH)

def install_keyboard(transport_id: str) -> bool:
    ''' Installs and enables IME keyboard.'''
    step = 0
    try:
        # Install ADBKeyboard
        cmd = ('adb', '-t', transport_id, 'install', f'{ROOT_PATH}/keyboard/ADBKeyboard.apk')
        subprocess.run(cmd, check=True, encoding='utf-8',
                                capture_output=True).stdout.strip()
        print("Installed ADBKeyboard")

        step = 1
        # Enable
        cmd = ('adb', '-t', transport_id, 'shell', 'ime', 'enable', 'com.android.adbkeyboard/.AdbIME')
        subprocess.run(cmd, check=True, encoding='utf-8',
                                capture_output=True).stdout.strip()
        step = 2
        # Set
        cmd = ('adb', '-t', transport_id, 'shell', 'ime', 'set', 'com.android.adbkeyboard/.AdbIME')
        subprocess.run(cmd, check=True, encoding='utf-8',
                                capture_output=True).stdout.strip()
        print("ADB Keyboard Installed, enabled and set!")
        return True
    except Exception as err:
        print(f"Failed to install IME keyboard on step: {step}",  err)
    return False

def send_text_ime(chars: str, transport_id: str):
    ''' Send text to IME keyboard. '''
    # chars = '的广告'
    charsb64 = str(base64.b64encode(chars.encode('utf-8')))[1:]
    os.system(f"adb -t {transport_id} shell am broadcast -a ADB_INPUT_B64 --es msg {charsb64}")


def send_unicode_ime(chars: str, transport_id: str):
    ''' Send unicode to IME keyboard. '''
    # To send 😸 Cat
    os.system(f"adb -t {transport_id} shell am broadcast -a ADB_INPUT_CHARS --eia chars {'128568,32,67,97,116'}")
