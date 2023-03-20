# Chicorobot

A discord bot for things todo with Chicory: A Colorful Tale

Read the code to lose 5 years of your life (that's a whopping 7% off!)

## Credit

High Res expressions by Plasmaflare

## To Run

- Python (you'll need it)

- Move an Export_Sprites (from UndertaleModTool, with bounds) into this dir.

- Some things require level_data to work (/save timelapse and screen palettes), I decided not to include a level_data with the repo. Put it in `data/level_data` if you want those things to work.

- Make a file called `TOKEN.txt` and put yo bot token innit, yknow https://discord.com/developers/applications

  - Make sure when you make your oauth url to invite your bot you tick app commands and bot.

- Install [gifsicle](https://www.lcdf.org/gifsicle/)

  - (put into `gifsicle/` dir if you want portable (windows only))

- Install [imagemagick](https://imagemagick.org/index.php)

  - put into `imagemagick/` dir, so that `imagemagick/convert.exe` is correct, if you want portable (windows only)

- For the following commands, on not windows replace `py` with `python` or `python3`

- Run `py -m pip install -r requirements.txt`

### For Testing

Discord takes about an hour to propagate global app commands, to speed up testing I sync to my testing server only.
- To make it sync to your server change line 49, so the id (`473976215301128193`) is the id of the server you wanna use this in (below is the line to change, make sure it looks like that)

```py
self.guild = discord.Object(473976215301128193) # msmg
```

- On first run (or any where you need to sync) `py bot.py test sync` to sync app commands

- For subsequent runs (with synced commands) `py bot.py test`

### For Regular

- On first run (or any where you need to sync) `py bot.py sync` to sync app commands

  - It can take up to an hour for global app commands to show up.

- For subsequent runs (with synced commands) `py bot.py`

### Note

On big updates and changes like those that add new commands you'll need to sync app commands again. This can be done with the /sync command or running the bot with sync arg again.

If you sync too much discord can get mad and rate limit you and also it does NOT help you at all so just sync when you need to.

## Make new sprites.json (optional)

`py sort_export.py`