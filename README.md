# Volume Settings
*  Set windows volume in VM to 100
*  In-game sound settings should look like this: https://gyazo.com/34f574700038c463de102db9a25a21a9
* *  "Cable Input" selected
* *  Master Volume at 50%
* *  Sound set to "High"
* *  All other sound effects turned off
* `audio_threshold` in `fishing_main.py` can be changed if needed but should be good if volume settings are consistent.

# Installing Dependencies
* Installing Python:
* * Install the latest version of python 3.9.x at `https://www.python.org/downloads/`
* * * One of the first menus in the installer has a checkbox to `add python to PATH`, make sure to check that box.
* `Shift+Right Click` in the `fishing_assistant` folder and click `Open Powershell here` and run `pip install -r requirements.txt`
* Installing VBCable Audio Driver:
* * Open the `fishing_assistant/misc_files/VBCable/VBCABLE_Driver_Pack43.zip` and run `VBCABLE_Setup_x64.exe` and click the driver install button at the bottom right of the pop-up window.
* * If you need to download the audio driver for some reason(the same zip file above):
* * * Install https://vb-audio.com/Cable/index.htm (todo: automate this? maybe it can be installed via cli?)
* Installing PyAudio:
* * It doesn't work if you try to install it through pip so you have to install the wheel manually.
* * I've included the .whl in the repo. In the same powershell window from above, enter: `pip install .\misc_files\PyAudio-0.2.11-cp39-cp39-win_amd64.whl`.
* * * It's worth noting that this file is specific to Python 3.9.


# Driver Notes
*  This is optional but should lead to a much lower chance of a ban. Set `use_driver = True` or `use_driver = False` to use virtual/pyautogui inputs.
*  Open a terminal AS ADMIN in the interception installer location `fishing_assistant\Interception\command line installer` and run `.\install-interception.exe /install`. Must reboot the vm after.

# Potential Issues
* Loud noises around character may trigger a caught fish reaction (not tested/proven)
* Bot will see a high volume level left over from the last run and think there is a fish caught
* * I believe to fix this, I need to clear the audio stream after every catch/reset.
