from win32api import GetSystemMetrics
from interception_py.interception import *
from loguru import logger

class EasyDriver:
    def __init__(self) -> None:
        # get screen size
        self.screen_width = GetSystemMetrics(0)
        self.screen_height = GetSystemMetrics(1)
        self.driver = interception()
        self.mouse_driver = self.get_driver_mouse()
        self.keyboard_driver = self.get_driver_keyboard()

    def get_driver_mouse(self):
        """Returns the first mouse device"""
        # loop through all devices and return the first mouse.
        mouse = 0
        for i in range(MAX_DEVICES):
            if interception.is_mouse(i):
                mouse = i
                return mouse

        # exit if we can't find a mouse.
        if (mouse == 0):
            logger.critical("No mouse found. Contact Gavin and disable the driver.")
            exit(0)


    def get_driver_keyboard(self):
        """Returns the first keyboard device"""
        # loop through all devices and return the first keyboard.
        for i in range(MAX_DEVICES):
            if interception.is_keyboard(i):
                keyboard = i
                return keyboard


    def move_mouse(self, screen_coords):
        """Moves the mouse to the screen coordinates and right clicks."""
        # we create a new mouse stroke, initially we use set right button down, we also use absolute move,
        # and for the coordinate (x and y) we use center screen
        mstroke = mouse_stroke(interception_mouse_state.INTERCEPTION_MOUSE_RIGHT_BUTTON_DOWN.value,
                                interception_mouse_flag.INTERCEPTION_MOUSE_MOVE_ABSOLUTE.value,
                                0,
                                int((0xFFFF * screen_coords[0]) / self.screen_width),
                                int((0xFFFF * screen_coords[1]) / self.screen_height),
                                0)
        self.driver.send(self.mouse_driver,mstroke) # we send the key stroke, now the right button is down

        mstroke.state = interception_mouse_state.INTERCEPTION_MOUSE_RIGHT_BUTTON_UP.value # update the stroke to release the button
        self.driver.send(self.mouse_driver,mstroke) #button right is up


    def press_key_driver(self, hotkey):
        """Presses and releases the provided key"""
        # Key down
        driver_press = key_stroke(hotkey, interception_key_state.INTERCEPTION_KEY_DOWN.value, 0)
        self.driver.send(self.keyboard_driver, driver_press)
        # Key up
        driver_press.state = interception_key_state.INTERCEPTION_KEY_UP.value
        self.driver.send(self.keyboard_driver, driver_press)