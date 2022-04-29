# Chicorobot

A discord bot for things todo with Chicory: A Colorful Tale

## Dog anims branch

This branch is a work in progress of dog animations (they don't work at all currently)

## To Run

Python (you'll need it)

Make a file called `TOKEN.txt` and put yo bot token innit

On not windows replace `py` with `python` or `python3`

Move an Export_Sprites (with bounds) into this dir

`py sort_export.py`

Install [image magick](https://imagemagick.org/script/download.php)

(put into imagemagick dir if you want portable)

`py -m pip install -r requirements.txt`

Modify bot.py and where it says

```py
TEST_GUILD = discord.Object(947898290735833128) # gay baby jail
```

change the id to the id of the server you wanna use this in

run `py bot.py`