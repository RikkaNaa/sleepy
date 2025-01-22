# coding: utf-8
'''
linux_device.py
在 Linux (KDE) 上获取窗口名称
by: @RikkaNaa
依赖: kdotool, requests
'''
from requests import post,get
from datetime import datetime
from time import sleep
from sys import stdout
from io import TextIOWrapper
import subprocess


# --- config start
SERVER = 'http://localhost:9010'
SECRET = 'wyf9test'
DEVICE_ID = 'device-1'
DEVICE_SHOW_NAME = 'MyDevice1'
CHECK_INTERVAL = 2
BYPASS_SAME_REQUEST = True
ENCODING = 'utf-8'  # 控制台输出所用编码，避免编码出错，可选 utf-8 或 gb18030
SKIPPED_NAMES = ['', 'plasmashell']  # 当窗口名为其中任意一项时将不更新
# --- config end

stdout = TextIOWrapper(stdout.buffer, encoding=ENCODING)  # https://stackoverflow.com/a/3218048/28091753
_print_ = print

def get_active_window_title():
    window_title = subprocess.check_output(["kdotool", "getactivewindow", "getwindowname"]).strip()
    return window_title.decode()

def print(msg: str, **kwargs):
    '''
    修改后的 `print()` 函数，解决不刷新日志的问题
    原: `_print_()`
    '''
    _print_(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {msg}', flush=True, **kwargs)


Url = f'{SERVER}/device/set'
last_window = ''
loop = 0

def do_update():
    global loop
    global last_window
    window = get_active_window_title()
    print(f'--- Window: `{window}`')

    # 判断是否在使用
    using = True
    if loop >= 900: # 默认30分钟
        using = False
    if window != last_window:
        loop = 0
        using = True

    # 检测重复名称
    if (BYPASS_SAME_REQUEST and window == last_window):
        print('window not change, bypass')
        loop += 1
        if using != False:
            return

    # 检查跳过名称
    for i in SKIPPED_NAMES:
        if i == window:
            print(f'* skipped: `{i}`')
            loop = 0
            return

    # POST to api
    print(f'POST {Url}')
    try:
        resp = post(url=Url, json={
            'secret': SECRET,
            'id': DEVICE_ID,
            'show_name': DEVICE_SHOW_NAME,
            'using': using,
            'app_name': window
        }, headers={
            'Content-Type': 'application/json'
        })
        if using == True:
            setstatus = get(url=f'{SERVER}/set/{SECRET}/0')
        else:
            setstatus = get(url=f'{SERVER}/set/{SECRET}/1')
        print(f'Response: {resp.status_code} - {resp.json()}')
    except Exception as e:
        print(f'Error: {e}')
    last_window = window


def main():
    while True:
        do_update()
        sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        # 如果中断则发送未在使用
        print(f'Interrupt: {e}')
        try:
            resp = post(url=Url, json={
                'secret': SECRET,
                'id': DEVICE_ID,
                'show_name': DEVICE_SHOW_NAME,
                'using': False,
                'app_name': f'{e}'
            }, headers={
                'Content-Type': 'application/json'
            })

            setstatus = get(url=f'{SERVER}/set/{SECRET}/1')
            print(f'Response: {resp.status_code} - {resp.json()}')
        except Exception as e:
            print(f'Error: {e}')
    except Exception as e:
        resp = post(url=Url, json={
            'secret': SECRET,
            'id': DEVICE_ID,
            'show_name': DEVICE_SHOW_NAME,
            'using': False,
            'app_name': f'{e}'
        }, headers={
            'Content-Type': 'application/json'
        })

        setstatus = get(url=f'{SERVER}/set/{SECRET}/1')
