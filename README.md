# Chicorobot

A discord bot for things todo with Chicory: A Colorful Tale

## To Run

Python (you'll need it)

Make a file called `TOKEN.txt` and put yo bot token innit, yknow https://discord.com/developers/applications

On not windows replace `py` with `python` or `python3`

Move an Export_Sprites (with bounds) into this dir

`py sort_export.py`

Install [image magick](https://imagemagick.org/script/download.php)

(put into imagemagick dir if you want portable (windows only))

`py -m pip install -r requirements.txt`

Discord takes about an hour to propagate global app commands, to speed this up I sync to the gbj server since it's the only one the bot will be used in.
To make it sync to your server change line 153 (currently, make sure it looks like below)

```py
guild = discord.Object(947898290735833128)
```

Change the id (`947898290735833128`) to the id of the server you wanna use this in

run `py bot.py`

Make sure when you make your oauth url you tick app commands.

## Credit

High Res expressions by Plasmaflare
