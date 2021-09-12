import sys
from utils.easy_driver import EasyDriver
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
bait_hotkey = 'x'
fishing_hotkey_driver = KEYBOARD_MAPPING[fishing_hotkey]
bait_hotkey_driver = KEYBOARD_MAPPING[bait_hotkey]
use_bait = True
found_fish = False
bobber_confidence = 0.80  # Increase or take a better bobber screenshot if the bot is clicking random places(not the bobber). You probably shouldn't ever need to decrease.

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
catch_timeout=((RATE / chunk * Max_Seconds) + 7)  # If you find that the bot times out and recasts before the cast is actually over, you can increase 7 by 1 until it's good.
audio_threshold = 25  # 20 should be fine based on readme.md volume settings but increase by 5 if it constantly thinks theres a catch before there really is.
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

# Crop game client down to fishing area to reduce false positives
top_offset = (game_size[2] // 2) - int((0.20 * game_size[2]))
bot_offset = (game_size[3] // 2) - int((0.30 * game_size[3]))
logger.info(f'Full Game Rect: {game_window_rect}')
game_window_rect = (
    game_window_rect[0] + bot_offset,
    game_window_rect[1] + top_offset,
    game_window_rect[2] - bot_offset,
    game_window_rect[3] - bot_offset
)
logger.info(f'Cropped Game Rect: {game_window_rect}')
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

# Counters
relog_counter = 0
no_bobber_counter = 0


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


def find_bobber(screenshot, template):
    methods = ['cv.TM_CCOEFF_NORMED']  #, 'cv.TM_CCORR_NORMED', 'cv.TM_SQDIFF', 'cv.TM_SQDIFF_NORMED'
    for meth in methods:
        method = eval(meth)
        # Apply template Matching
        res = cv.matchTemplate(screenshot, template, method)
        (min_val, max_val, min_loc, max_loc) = cv.minMaxLoc(res)
        return (min_val, max_val, min_loc, max_loc)


def print_stats(start_time, fish_caught, bait_used, rods_cast):
    time_ran = get_duration(then=start_time, now=datetime.now(), interval='default')
    gold_earned = fish_caught * 10
    logger.success('-----------------------')
    logger.success('Progress Report:')
    logger.success(f'Time Ran: {time_ran} minute(s)')
    logger.success(f'Estimated Gold Earned: {gold_earned}g')
    logger.success(f'Rods Cast: {rods_cast}')
    logger.success(f'Fish Caught: {fish_caught}')
    logger.success(f'Bait Used: {bait_used}')
    logger.success('-----------------------')


# Initialize Audio stream to detect bobber splash
stream = p.open(format = FORMAT,
                channels = CHANNELS,
                rate = RATE,
                input = True,
                output = True,
                frames_per_buffer = chunk,
                input_device_index= audio_devices['input_device_index'],
                output_device_index = audio_devices['output_device_index'])

# Initialize Driver
if use_driver:
    driver = EasyDriver()

# Initialize bot
logger.add('log.txt', level="INFO")
start_time = datetime.now()
time.sleep(1 + random.random())
SetForegroundWindow(game_window_handle)
if use_bait:
    driver.press_key_driver(bait_hotkey_driver)
    bait_time = datetime.now()

with mss.mss() as sct:
    while True:
        if use_bait:
            time_since_bait = get_duration(then=bait_time, now=datetime.now(), interval='minutes')
            if time_since_bait >= 30:  # Fishing bait has expired
                logger.info('Applying fishing bait...')
                driver.press_key_driver(bait_hotkey_driver)
                bait_used += 1
                bait_time = datetime.now()

                # "hack" to print stats every 30 minutes without repeating code
                print_stats(start_time, fish_caught, bait_used, rods_cast)

        # Cast fishing rod
        driver.press_key_driver(fishing_hotkey_driver)
        rods_cast += 1
        time.sleep(2.7 + random.random())

        # Take game screenshot
        tmp_screenshot = sct.grab(game_window_rect)
        screenshot = cv.cvtColor(np.array(tmp_screenshot), cv.COLOR_BGR2GRAY)

        # Detect fishing bobber
        min_val, max_val, min_loc, max_loc = find_bobber(screenshot, template)
        max_val = round(max_val, 2)

        # Show game screenshot. Useful for debugging.
        logger.debug('Showing game screenshot before checking bobber confidence')
        cv.imshow('WoW', screenshot)
        key = cv.waitKey(1)
        if key == ord('q'):
            cv.destroyAllWindows()
            sys.exit()

        if max_val > bobber_confidence:
            
            logger.success(f'Found bobber at {max_loc} with confidence {max_val}.')
            top_left = max_loc
            bottom_right = (top_left[0] + w, top_left[1] + h)
            bobber_center = ((top_left[0] + w / 2) + game_window_rect[0], (top_left[1] + h / 2) + game_window_rect[1])

            # Draw rectangle around bobber
            logger.debug('Drawing rectangle around found bobber.')
            cv.rectangle(screenshot, top_left, bottom_right, (0,255,0), 1)
            # Reset counter for next cast
            no_bobber_counter = 0

            # Listen to audio queue for fish catch.
            while True:
                # Show game screenshot with bobber marked. Useful for debugging.
                cv.imshow('WoW', screenshot)
                key = cv.waitKey(1)
                if key == ord('q'):
                    cv.destroyAllWindows()
                    sys.exit()
                
                # Get audio level from game
                try:
                    input = stream.read(chunk)
                    rms_value = rms(input)
                except:
                    continue
                
                # if rms_value >= 10:  # This will never print if the user has their sound low.
                #     logger.debug(f'Sound Level: {rms_value}')
                if found_fish and rms_value < 1.0:
                    found_fish = False

                if not found_fish and rms_value > audio_threshold:
                    logger.success("Found catch!")
                    time.sleep(0.150 + random.random())
                    # Right click the bobber to collect the loot.
                    # Wrapped in try block because pyHM.right_click() gives an invalid inputs ValueError
                    try:
                        driver.move_mouse(bobber_center)
                    except ValueError:
                        logger.warning("I don't think we'll ever hit this. Breaking audio loop")
                        break
                    # Successfully clicked what we think is the bobber location (not sure how to confirm yet)
                    fish_caught += 1
                    logger.info(f'Fish Caught: {fish_caught}')
                    time.sleep(1 + random.random())
                    found_fish = True
                    break
                if catch_time > catch_timeout:
                    no_fish_casts += 1
                    logger.warning("Timed out, never detected a splash.")

                    # If we miss 5 catches in a row we can probably assume something is really wrong like our in-game pov is messed up or we're logged out
                    # This assumes we got logged out and attempts to log us back in.
                    # If it's a temporary problem and we're in-game hitting 'enter' I could see us getting stuck in the chatbox. Maybe unbind 'enter' on the bot toons
                    relog_counter += 1
                    if relog_counter >= 5:  # Assumes we got logged out and we'll try to reconnect
                        logger.warning("We've failed to catch 5 fish in a row. Activating failsafe.")
                        for i in range(0,4):  # Hit enter 3 times (Max amount needed to get back to the game from a recoverable login screen state.)
                            driver.press_key_driver(KEYBOARD_MAPPING['enter'])
                            time.sleep(5)
                        relog_counter = 0
                    break
                else:
                    # Successful catch, reset the counter or else the failsafe will activate at 5 overall missed splashes instead of 5 in a row.
                    relog_counter = 0
                # Adds and resets timer for how long the fishing rod has been in the water for its current cast. (used for timeout/reset)
                catch_time += 1
            catch_time = 0
            #p.close(stream)
        # template matching couldn't detect the bobber. Confidence may need to be lowered or new screenshot.
        else:
            logger.warning(f"Couldn't find bobber. Highest confidence: {max_val} at {max_loc}.")
            no_bobber_counter += 1

            if no_bobber_counter >= 5:
                logger.critical("Couldn't find the bobber 5 times in a row. Exiting the bot.")
                sys.exit(1)
