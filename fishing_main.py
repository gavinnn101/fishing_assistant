import cv2 as cv
import math
import mss
import numpy as np
import pyaudio
import pyautogui as pg
import random
import struct
import sys
import time
from datetime import datetime
from interception_py.interception import *
from loguru import logger
from pyHM import mouse
from win32gui import FindWindow, GetWindowRect, GetClientRect, SetForegroundWindow
from utils.datetime_util import get_duration
from utils.easy_driver import EasyDriver
from utils.key_codes import KEYBOARD_MAPPING


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
bobber_confidence = 0.70  # Decreasing below 0.65 will probably give false positives. Take a better screenshot to get higher confidence.

template = cv.imread('bobber.jpg', 0)
w, h = template.shape[::-1]
# Fishing variables
#################

####################
# Shopping variables
use_auto_vendor = True
mammoth_hotkey = 'i'
target_hotkey = 'k'
interact_hotkey = 'l'
vendor_interval = 180  # Minutes between selling trash items
mammoth_hotkey_driver = KEYBOARD_MAPPING[mammoth_hotkey]
target_hotkey_driver = KEYBOARD_MAPPING[target_hotkey]
interact_hotkey_driver = KEYBOARD_MAPPING[interact_hotkey]
# Shopping variables
####################

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
catch_timeout=((RATE / chunk * Max_Seconds) + 9)  # If you find that the bot times out and recasts before the cast is actually over, you can increase 7 by 1 until it's good.
audio_threshold = 18  # 20 should be fine based on readme.md volume settings but increase by 5 if it constantly thinks theres a catch before there really is.
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


def auto_vendor(mammoth_hotkey, target_hotkey, interact_hotkey):
    """Vendors non-valuable fish via mount. Only tested with traveler's tundra mammoth and 'Vendor' addon."""
    # Get on mount
    logger.debug('getting on mount')
    driver.press_key_driver(mammoth_hotkey)
    time.sleep(3 + random.random())
    # Target shop npc with target macro
    logger.debug('targetting npc')
    driver.press_key_driver(target_hotkey)
    time.sleep(3 + random.random())
    # Interact with target
    logger.debug('interacting with npc / opening shop')
    driver.press_key_driver(interact_hotkey)
    time.sleep(3 + random.random())
    # Vendor addon should now sell all of the non-valuable fish
    logger.debug('about to sleep while Vendor addon sells trash')
    time.sleep(5 + random.random())
    # Close shop window
    logger.debug('closing shop window')
    driver.press_key_driver(KEYBOARD_MAPPING['esc'])
    time.sleep(3 + random.random())



def bank_fish(gbank_hotkey, ):
    pass
    # Guild bank has a 1 hour cooldown and is active for 5 minutes once used.
    # We should call auto_vendor() before bank_fish().
    # we should:
        # In the main loop check if X hours has passed(I would say maybe 8)
        # If so, call bank_fish()
            # press gbank_hotkey
            # template match for the guild logo(?) on the guild bank
            # Once found, call driver to move mouse to it and right click (same as fishing)
            # Once in the bank interface, I think we'll need to give each bank tab an icon and template match against it
            # Once we find it and click into the bank tab, we can open our inventory
            # Ideally we use an addon to auto-deposit the fish like TSM. Otherwise we'd have to for loop template match a fish icon against our inventory until it cant find anymore.
            # Close the bank interface(probably with esc) and sleep for ~3-5 minutes to make sure the gbank is gone from our view.
            # Continue fishing



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
    logger.debug(f'Keyboard Driver: {driver.keyboard_driver}')
    logger.debug(f'Mouse Driver: {driver.mouse_driver}')

# Initialize bot
logger.add('log.txt', level="INFO") # Can change to DEBUG
start_time = datetime.now()
time.sleep(1 + random.random())
SetForegroundWindow(game_window_handle)
if use_bait:
    driver.press_key_driver(bait_hotkey_driver)
    bait_time = datetime.now()
if use_auto_vendor:
    vendor_time = datetime.now()

with mss.mss() as sct:
    while True:
        if use_auto_vendor:
            time_since_vendor = get_duration(then=vendor_time, now=datetime.now(), interval='minutes')
            if time_since_vendor >= vendor_interval:
                logger.info('Now vendoring trash...')
                time.sleep(5)
                auto_vendor(mammoth_hotkey_driver, target_hotkey_driver, interact_hotkey_driver)
                vendor_time = datetime.now()
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

        if max_val >= bobber_confidence:
            
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

                # Reset found_fish after bobber noises subside (rms_value < 1.0)
                if found_fish and rms_value < 1.0:
                    logger.debug('Now listening for catch.')
                    found_fish = False

                if not found_fish and rms_value > 1.0:
                    # logger.debug(f'Checking if {rms_value} is higher than {audio_threshold}')
                    if rms_value >= audio_threshold:
                        logger.success("Found catch!")
                        time.sleep(0.150 + random.random())
                        # Right click the bobber to collect the loot.
                        # Wrapped in try block because pyHM.right_click() gives an invalid inputs ValueError
                        try:
                            driver.move_mouse(bobber_center)
                        except ValueError:
                            logger.warning("I don't think we'll ever hit this. Breaking audio loop from mailed driver.mouse_move")
                            break
                        # Successfully clicked what we think is the bobber location (not sure how to confirm yet)
                        fish_caught += 1
                        logger.info(f'Fish Caught: {fish_caught}')
                        time.sleep(1 + random.random())
                        found_fish = True
                        # Successful catch, reset the counter or else the failsafe will activate at 5 overall missed splashes instead of 5 in a row.
                        relog_counter = 0
                        break
                if catch_time >= catch_timeout:
                    no_fish_casts += 1
                    logger.warning(f"Never detected a splash. Fish timeouts: {no_fish_casts}.")
                    break
                # Fish hasn't been caught yet. Add to timer
                catch_time += 1
            catch_time = 0
        #p.close(stream)
        # template matching couldn't detect the bobber. Confidence may need to be lowered or new screenshot.
        else:
            logger.warning(f"Couldn't find bobber. Highest confidence: {max_val} at {max_loc}.")
            no_bobber_counter += 1

            if no_bobber_counter >= 5:
                logger.critical("Couldn't find the bobber 5 times in a row, activating failsafe.")
                logger.info('Taking screenshot before exiting.')
                sct.shot(output="debug_screenshot.png")
                logger.info('Screenshot saved. Now exiting...')
                sys.exit(1)
