import sys
import cv2 as cv
import numpy as np
import mss
import pyautogui as pg
import time
import pyaudio
import struct
import math
import random
from win32gui import FindWindow, GetWindowRect, GetClientRect, SetForegroundWindow
from loguru import logger
from pyHM import mouse
from interception_py.interception import *
from win32api import GetSystemMetrics
from utils.key_codes import KEYBOARD_MAPPING
from datetime import datetime
from utils.datetime_util import get_duration


def get_audio_devices():
    """Returns the default playback device (for use as output) and virtual audio CABLE OUTPUT (for use as input). Make sure to set virtual audio in WoW."""
    p = pyaudio.PyAudio()
    virtual_audio_name = 'CABLE Output'
    output_device_index = p.get_default_output_device_info().get('index')
    output_device_name = p.get_default_output_device_info().get('name')
    logger.success(f'Using {output_device_name} as the output device with the index {output_device_index}.')

    # Find the virtual audio driver index
    for i in range(p.get_device_count()):
        device = p.get_device_info_by_index(i)
        if virtual_audio_name in device.get('name'):
            input_device_index = device.get('index')
            logger.success(f'Using {virtual_audio_name} as the virtual input device with the index {input_device_index}.')
            break
    
    return {'output_device_index': output_device_index, 'input_device_index': input_device_index}


#################
# Fishing variables
use_driver = True
fishing_hotkey = 'z'
fishing_hotkey_driver = KEYBOARD_MAPPING[fishing_hotkey]
bait_hotkey = 'x'
bait_hotkey_driver = KEYBOARD_MAPPING[bait_hotkey]
use_bait = True
found_fish = False
bobber_confidence = 0.40

template = cv.imread('bobber.jpg', 0)
w, h = template.shape[::-1]
# Fishing variables
#################

#################
# Audio variables
p = pyaudio.PyAudio()
SHORT_NORMALIZE = (1.0/32768.0)
chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
swidth = 2
Max_Seconds = 15
catch_time=0
catch_timeout=((RATE / chunk * Max_Seconds) + 5)
audio_threshold = 30
audio_devices = get_audio_devices()
# Audio variables
#################

#######################
# Game Client Variables
game_window_name = "World of Warcraft"
game_window_class = "GxWindowClass"
game_window_handle = FindWindow(game_window_class, game_window_name)
game_window_rect = GetWindowRect(game_window_handle)  # left, top, right, bottom
game_size = GetClientRect(game_window_handle)
# Game Client Variables
#######################

###################
# Fishing Stats
time_ran = 0
estimated_gold = 0
fish_caught = 0
no_fish_casts = 0
bait_used = 0
rods_cast = 0
# Fishing Stats
###################


def rms(frame):
    """
    I Didn't write this but it looks like it takes in audio frames/chunk
    and returns the sound level in a 0.00 format
    """
    count = len(frame)/swidth
    format = "%dh"%(count)
    # short is 16 bit int
    shorts = struct.unpack(format, frame)

    sum_squares = 0.0
    for sample in shorts:
        n = sample * SHORT_NORMALIZE
        sum_squares += n*n
    # compute the rms
    rms = math.pow(sum_squares / count, 0.5)
    return rms * 1000

def get_driver_mouse():
    # loop through all devices and check if they correspond to a mouse
    mouse = 0
    for i in range(MAX_DEVICES):
        if interception.is_mouse(i):
            mouse = i
            return mouse

    # exit if we can't find a mouse.
    if (mouse == 0):
        logger.critical("No mouse found. Contact Gavin and disable the driver.")
        exit(0)


def get_driver_keyboard():
    # loop through all devices and check if they correspond to a mouse
    keyboard = 0
    for i in range(MAX_DEVICES):
        if interception.is_keyboard(i):
            keyboard = i
            return keyboard


def move_mouse(bobber_loc, driver, mouse_driver):
    """Moves mouse to b"""
    # get screen size
    screen_width = GetSystemMetrics(0)
    screen_height = GetSystemMetrics(1)
    # we create a new mouse stroke, initially we use set right button down, we also use absolute move,
    # and for the coordinate (x and y) we use center screen
    mstroke = mouse_stroke(interception_mouse_state.INTERCEPTION_MOUSE_RIGHT_BUTTON_DOWN.value,
                            interception_mouse_flag.INTERCEPTION_MOUSE_MOVE_ABSOLUTE.value,
                            0,
                            int((0xFFFF * bobber_loc[0]) / screen_width),
                            int((0xFFFF * bobber_loc[1]) / screen_height),
                            0)
    driver.send(mouse_driver,mstroke) # we send the key stroke, now the right button is down

    mstroke.state = interception_mouse_state.INTERCEPTION_MOUSE_RIGHT_BUTTON_UP.value # update the stroke to release the button
    driver.send(mouse_driver,mstroke) #button right is up


def press_key_driver(hotkey, driver, keyboard_driver):
    # Key down
    driver_press = key_stroke(hotkey, interception_key_state.INTERCEPTION_KEY_DOWN.value, 0)
    driver.send(keyboard_driver, driver_press)
    # Key up
    driver_press.state = interception_key_state.INTERCEPTION_KEY_UP.value
    driver.send(keyboard_driver, driver_press)


def print_stats(start_time, fish_caught, bait_used, rods_cast):
    time_ran = get_duration(start_time, interval='minutes')
    gold_earned = fish_caught * 10
    logger.success('-----------------------')
    logger.success(f'Time Ran: {time_ran} minute(s)')
    logger.success(f'Estimated Gold Earned: {gold_earned}g')
    logger.success(f'Rods Cast: {rods_cast}')
    logger.success(f'Fish Caught: {fish_caught}')
    logger.success(f'Bait Used: {bait_used}')
    logger.success('-----------------------')


# Audio stream to detect bobber splash
stream = p.open(format = FORMAT,
                channels = CHANNELS,
                rate = RATE,
                input = True,
                output = True,
                frames_per_buffer = chunk,
                input_device_index= audio_devices['input_device_index'],
                output_device_index = audio_devices['output_device_index'])


# Initialize Drivers
if use_driver:
    driver = interception()
    mouse_driver = get_driver_mouse()
    keyboard_driver = get_driver_keyboard()

# Initialize bot
logger.add('log.txt', level="INFO")
start_time = datetime.now()
time.sleep(1 + random.random())
SetForegroundWindow(game_window_handle)
if use_bait:
    press_key_driver(bait_hotkey_driver, driver, keyboard_driver)
    # pg.press(bait_hotkey)
    bait_time = datetime.now()

try:
    with mss.mss() as sct:
        while True:
            if use_bait:
                if get_duration(bait_time, interval='minutes') >= 30:
                    logger.info('Applying fishing bait...')
                    press_key_driver(bait_hotkey_driver, driver, keyboard_driver)
                    # pg.press(bait_hotkey)
                    bait_used += 1
                    bait_time = datetime.now()
                    print_stats(time_ran, fish_caught, bait_used, rods_cast)
            # Cast fishing rod
            press_key_driver(fishing_hotkey_driver, driver, keyboard_driver)
            # pg.press(fishing_hotkey)
            rods_cast += 1
            time.sleep(2.7 + random.random())
            # Take game screenshot
            tmp_screenshot = sct.grab(game_window_rect)
            screenshot = cv.cvtColor(np.array(tmp_screenshot), cv.COLOR_BGR2GRAY)
            # Detect fishing bobber
            methods = ['cv.TM_CCOEFF_NORMED']#, 'cv.TM_CCORR_NORMED', 'cv.TM_SQDIFF', 'cv.TM_SQDIFF_NORMED']
            for meth in methods:
                method = eval(meth)
                # Apply template Matching
                res = cv.matchTemplate(screenshot, template, method)
                min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
                
                if max_val > bobber_confidence:
                    logger.success(f'Found bobber at {max_loc}')
                    top_left = max_loc
                    bottom_right = (top_left[0] + w, top_left[1] + h)
                    bobber_center = ((top_left[0] + w / 2) + game_window_rect[0], (top_left[1] + h / 2) + game_window_rect[1])

                    # Move cursor to the center of the bobber
                    # try:
                    #     mouse.move(bobber_center[0], bobber_center[1])
                    # except ValueError:
                    #     logger.warning(f'Value error when trying to move mouse to bobber. Coords: {bobber_center[0]}, {bobber_center[1]}')
                    #     break

            # Detect caught fish via audio queue
            while True:
                try:
                    input = stream.read(chunk)
                    rms_value = rms(input)
                except:
                    continue
                
                if rms_value >= 10:  # This will never print if the user has their sound low.
                    logger.info(f'Sound Level: {rms_value}')
                if found_fish and rms_value < audio_threshold:
                    found_fish = False

                if not found_fish and rms_value > audio_threshold:
                    logger.success("Found catch!")
                    time.sleep(0.150 + random.random())
                    # Right click the bobber to collect the loot.
                    # Wrapped in try block because pyHM.right_click() gives an invalid inputs ValueError
                    try:
                        move_mouse(bobber_center, driver, mouse_driver)
                    except ValueError:
                        break
                    fish_caught += 1
                    logger.info(f'Fish Caught: {fish_caught}')
                    time.sleep(1 + random.random())
                    found_fish = True
                    break
                if catch_time > catch_timeout:
                    no_fish_casts += 1
                    logger.warning("Timed out, never detected a splash.")
                    break
                catch_time = catch_time + 1
            catch_time = 0
            #p.close(stream)
except Exception as e:
    logger.error(e)
    print_stats(start_time, fish_caught, bait_used, rods_cast)
    exit(0)
