# Volume Settings
*  Install https://vb-audio.com/Cable/index.htm (todo: automate this? maybe it can be installed via cli?)
*  Set windows volume in VM to 100
*  In-game sound settings should look like this: https://gyazo.com/34f574700038c463de102db9a25a21a9
* *  "Cable Input" selected
* *  Master Volume at 50%
* *  Sound set to "High"
* *  All other sound effects turned off
* *  `audio_threshold` can be changed if needed but should be good if volume settings are consistent.

# Installing Dependencies
* Open a terminal in the folder and run `pip install -r requirements.txt`
* Installing PyAudio
* * It doesn't work if you try to install it through pip so you have to install the wheel manually.
* * I've included the .whl in the repo. run `pip install .\PyAudio-0.2.11-cp39-cp39-win_amd64.whl`.
* * * It's worth noting that this file is specific to Python 3.9.


# Driver Notes
*  This is optional but should lead to a much lower chance of a ban. Set `use_driver = True` or `use_driver = False` to use virtual/pyautogui inputs.
*  Open a terminal in the interception installer location (fishing_bot/interception/Command Line Installer) and run `.\install-interception \install`. Must reboot the vm after.

# Potential Issues
* Loud noises around character may trigger a caught fish reaction (not tested/proven)
* Bot will see a high volume level left over from the last run and think there is a fish caught
* * I believe to fix this, I need to clear the audio stream after every catch/reset.
