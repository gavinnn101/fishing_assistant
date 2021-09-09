# Introduction
Please follow the below sections in order CAREFULLY and let me know if you have any questions or run into any problems.


This is just a personal project that I'm having fun with above all else. I'm working on it when I feel like it, not selling it, and sharing it with friends, privately, for free. My goal for this project is to be able to easily run and manage a large amount of fishing bots and not get banned. 

* security:
* * Interception Driver - The security largely comes from using the interception driver that scans for your real keyboard/mouse and fakes the input from there instead of virtual inputs that most bots use and are typically detected. - done/implemented!
* * Code Obfuscation - The code will by dynamically changed before each run to hopefully help against any signature checks
* * Breaks - You will be able to set up break schedules for your bots so that they will log out after (ex: 30-45 minutes) for (ex: 5-15 minutes) and then after 2 hours for 1 hour, etc. In my experience, playtime hasn't seemed to make much of a difference in bans for me but I do plan to implement it just incase. 
* * AI Generated Conversations - I have access to OpenAI's GPT-3 which is an AI that can generate conversations/responses based on input. With this project largely being about running many(2+) bots at once, I plan to implement a feature where your bots will randomly have fake AI generated, WoW related(and other) conversations in guild chat or whispers to look less bot like. 
* * * This same idea could be used to respond to random players that whisper your bot but I'm leaning towards just ignoring them. To be decided... Can always be optional


* Bot Management:
* * Managing the bots at scale will come from the next part of the project that I'm working on. I'm building a website where every user will be able to log into their account and manage all of their bots:
* * You will be able to start and stop the bots at any time
* * See real-time stats for each individual bot (run time, gold earned, fish caught, etc)
* * See real-time screenshots for each individual bot
* * See real-time logs for each individual bot
* * Send a message in-game as your bot character from the website (to implement later)
* * automatically vendor trash items(bait/greys/etc)(provided you have a vendor mount like a mammoth)
* * Automatically relog into the game if disconnected and resume fishing
* * Feature Enhancement: Detect if it's reset day and sleep until servers are online


If you think of any features you feel would be highly beneficial that aren't on either of these lists, feel free to let me know :)


# Installing Dependencies
* Installing Python:
* * Install the latest version of python 3.9.x at `https://www.python.org/downloads/`
* * * The first menu in the installer has a checkbox to `Add Python 3.9 to PATH`, make sure to check that box.
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

# Volume Settings
*  Set windows volume in VM to 100
*  In-game sound settings should look like this: https://gyazo.com/34f574700038c463de102db9a25a21a9
* *  "Cable Input" selected
* *  Master Volume at 50%
* *  Sound set to "High"
* *  All other sound effects turned off
* `audio_threshold` in `fishing_main.py` can be changed if needed but should be good if volume settings are consistent.

# Potential Issues
* Loud noises around character may trigger a caught fish reaction (not tested/proven)
* Bot will see a high volume level left over from the last run and think there is a fish caught
* * I believe to fix this, I need to clear the audio stream after every catch/reset.
