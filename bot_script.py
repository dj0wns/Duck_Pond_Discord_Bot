import discord
import asyncio
import random
import os
import datetime
import imgkit
import tempfile
import io
import PIL
import operator
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import glob

from open_search import OpenSearch, OpenSearchError, SearchObjectError
import sqldb

fpath=os.path.realpath(__file__)
path=os.path.dirname(fpath)
DB_FILE=path+"/local.db"

auction_mode = False
auction_item = ""
auction_dict = {}

prof_map = {
  'none' : 0,
  'alchemy' : 1,
  'blacksmithing' : 2,
  'enchanting' : 3,
  'engineering' : 4,
  'herbalism' : 5,
  'leatherworking' : 6,
  'mining' : 7,
  'skinning' : 8,
  'tailoring' : 9
}

#inverse and with correct caps
inv_prof_map = {
  0 : 'None',
  1 : 'Alchemy',
  2 : 'Blacksmithing',
  3 : 'Enchanting',
  4 : 'Engineering',
  5 : 'Herbalism',
  6 : 'Leatherworking',
  7 : 'Mining',
  8 : 'Skinning',
  9 : 'Tailoring'
}
def days_since_join(join_date):
  join = datetime.datetime.strptime(join_date,'%Y-%m-%d %H:%M:%S.%f')
  diff = datetime.datetime.now() - join
  days = diff.days
  return days

def html_header():
  return '<html><body><div style="width:600px;">\n'

def html_footer():
  return '</div></body></html>\n'

def random_num():
  return random.randint(0,100)

async def send_html(channel,html):
  img = imgkit.from_string(html, False)
  tf = tempfile.NamedTemporaryFile(suffix='.jpg')
  tf.write(img)
  tf.flush()
  await channel.send(file=discord.File(tf.name,"file.jpg"))
  tf.close()


async def commands(channel):
  #make rich embed
  message=( 
            " - !hello - says hello back!\n"
            " - !quack - Quacks!\n"
            " - !forthehorde - The alliance will tremble beneath these fearsome warcries!\n"
            " - !commands - displays this helpful dialogue\n"
            " - !item [itemname] - if exists, returns an infobox detailing the named item\n"
            " - !spell [spellname] - if exists, returns an infobox detailing the named spell\n"
            " - !need - rolls need from 0-100\n"
            " - !greed - rolls greed from 0-100\n"
            " - !list - lists dkp totals of all members\n"
            " - !dkp - returns how much dkp you have\n"
            " - !countdown - returns how much time till classic release\n"
            " - !paladin - asserts your role as a horde paladin\n"
            " - !classlist - list the number of each class currently in the guild\n"
            " - !events - list all running and upcoming events\n"
            " - !blacklist - list current offense on the blacklist\n"
          )
  events=(
          "These commands are to be used during events:\n"
          " - !checkin - check in to the current running event\n"
          " - !bid [amount] - bids an amount of dkp in the current auction - make sure to private message the bot for anonymity\n"
        )
  character=(
            "These commands modify or display information about your character:\n"
            " - !setprof1 [profession]- sets your first profession or none for no profession\n"
            " - !setprof2 [profession]- sets your second profession or none for no profession\n"
            " - !getprofs - Lists your currently chosen professions\n"
            " - !addrole [heal,dps,tank] - Adds a role you plan on playing and being geared for\n"
            " - !removerole [heal,dps,tank] - Removes a role from your character\n"
            " - !setname [name] - set the name of your character for armory lookups and other references\n"
            " - !setclass [class] - set your primary class\n"
            " - !stats - prints your stats sheet\n"
            " - !days - prints how many days you have been a member of the guild\n"

          )
  lootmaster=( 
            "These commands only work if you have the \"Loot Master\" role:\n"
            " - !createevent [start time (Y-M-D-H:M) in EST time] [duration in hours] [type (casual, raid, pvp, pve, tournament)] [Min DKP Award] [name] [Description]\n"
            " - !removeevent [eventid] - Remove an event from the table\n"
            " - !startevent [eventid] - Start an event early, and end any other events currently running\n"
            " - !endevent - End the currently running event and distribute dkp\n"
            " - !adddkp [user]... [amount] - adds amount of dkp to users - uses discord name or char name\n"
            " - !spenddkp [user] [amount] - spend a users dkp for winning an auction - for keeping track of expenditures for null-value\n"
            " - !unspenddkp [user] [amount] - revert a mistake dkp spend for an auction\n"
            " - !removedkp [user]... [amount] - removes amount of dkp from users in the event of fixing or punishment - uses discord name or char name\n"
            " - !auction [itemname] - starts an auction for [itemname] users my private message RoboDuck to bid\n"
            )
  moderation=(
            "These commands are for moderating players - Officers only:\n"
            " - !didnotshow [eventid] [name] - note that a checked in player did not show so they dont get points\n"
            " - !forcecheckin [name] - force check in a player if they are on the blacklist\n"
            " - !addblacklist [user] [days] [offense description] - Add a player to the blacklist to prevent them from checking into events and earning dkp\n"
            " - !removeblacklist [blacklist id] - Revmove an offense from the blacklist\n"
            " - !fullblacklist - Lists as much of the history of the blacklist as possible\n"
            )

  embedMessage = discord.Embed()
  embedMessage.add_field(name="General Commands", value=message)
  embedMessage.add_field(name="Event Commands", value=events)
  embedMessage.add_field(name="Character Commands", value=character)
  embedMessage.add_field(name="Loot Master Commands", value=lootmaster)
  embedMessage.add_field(name="Moderation Commands", value=moderation)
  await channel.send(embed=embedMessage)

async def hello(channel, name):
  await channel.send('Hi ' + name + "!")

async def quack(channel, name):
  await channel.send('Quack!')

async def forthehorde(channel, name):
  messages = ["For the Horde!",
              "Lok-tar ogar!",
              "Quack! Quack! Quaaaaaack!",
              "Death to the enemies of the Horde!"]
  await channel.send(random.choice(messages))

async def need(channel, author, name):
  sqldb.increment_need(author.id)
  await channel.send(name + " need rolled a " + str(random_num()) + "!")

async def greed(channel, author, name):
  sqldb.increment_greed(author.id)
  await channel.send(name + " greed rolled a " + str(random_num()) + "!")

async def dkp(channel, author, name):
  await channel.send(name + " you have " + str(sqldb.get_dkp(author.id)) + " dkp!")

async def paladin(channel):
  await channel.send(file=discord.File(path + "/paladin.png","paladin.png"))

async def stats(channel, author, name):
  result = sqldb.get_player(author.id)
  main = (result[5] if not result[5] == "" else "unknown")
  dkp = str(result[2])
  need= str(result[3])
  greed = str(result[4])
  days = str(days_since_join(result[6]))
  avatar = author.avatar_url_as(static_format='png',size=128)
  avatarbytes = await avatar.read()
  avatarImage = Image.open(io.BytesIO(avatarbytes))
  im = Image.open(path + "/background.png")
  im.paste(avatarImage,(31,31))
  font = ImageFont.truetype("/usr/share/fonts/noto/NotoSerifDisplay-Light.ttf", 32)
  draw = ImageDraw.Draw(im)
  draw.text((210, 25),name,(0,0,0),font=font)
  draw.text((240, 60),main,(0,0,0),font=font)
  draw.text((190, 120),dkp + " dkp",(0,0,0),font=font)
  draw.text((320, 120),greed,(0,0,0),font=font)
  draw.text((406, 120),need,(0,0,0),font=font)
  imgbytes = io.BytesIO()
  im.save(imgbytes, format='PNG')
  imgbytes = imgbytes.getvalue()
  tf = tempfile.NamedTemporaryFile(suffix='.png')
  tf.write(imgbytes)
  tf.flush()
  await channel.send(file=discord.File(tf.name,"file.png"))
  tf.close()

async def listAcc(client,channel):
  #make sure all members are accounted for
  results=sqldb.print_account_records()
  if results == None: return
  message = html_header()
  message += '<p style="font-size:40px">'
  for result in results:
    if not client.user.id == result[1]:
      user=channel.guild.get_member(result[1])
      #if user isnt in discord
      if user == None:
        continue
      message += (user.display_name + ":<br>" 
                 + (result[5] if not result[5] == "" else "unknown")
                 + "&emsp;" + str(result[2]) + " dkp<br>" 
                 + "&emsp;" + str(result[3]) + " need rolls<br>"
                 + "&emsp;" + str(result[4]) + " greed rolls<br>")
  
  message += html_footer()
  await send_html(channel,message)

async def countdown(channel):
  release = datetime.datetime(2019, 8, 26, 18)
  current = datetime.datetime.now()
  if release > current:
    togo = release - current
    await channel.send("There are only " + str(togo.days) + " days and " + str(togo.seconds//3600) + " hours until WoW Classic is released!")
  else:
    togo = current - release
    await channel.send("WoW Classic was released  " + str(togo.days) + " days and " + str(togo.seconds//3600) + " hours ago! Lok'tar Ogar!")
    

async def setname(channel, author, name, accname):
  sqldb.set_name(author.id,accname)
  await channel.send(name + "'s character name is now: " + accname)

async def setclass(channel, author, name, classname, client):
  classname = classname.lower()
  addlist = []
  removelist = []
  if classname == "warrior":
    addlist.append(discord.utils.get(channel.guild.roles, name="Warrior"))
  else:
    removelist.append(discord.utils.get(channel.guild.roles, name="Warrior"))
  if classname == "druid":
    addlist.append(discord.utils.get(channel.guild.roles, name="Druid"))
  else:
    removelist.append(discord.utils.get(channel.guild.roles, name="Druid"))
  if classname == "mage":
    addlist.append(discord.utils.get(channel.guild.roles, name="Mage"))
  else:
    removelist.append(discord.utils.get(channel.guild.roles, name="Mage"))
  if classname == "warlock":
    addlist.append(discord.utils.get(channel.guild.roles, name="Warlock"))
  else:
    removelist.append(discord.utils.get(channel.guild.roles, name="Warlock"))
  if classname == "hunter":
    addlist.append(discord.utils.get(channel.guild.roles, name="Hunter"))
  else:
    removelist.append(discord.utils.get(channel.guild.roles, name="Hunter"))
  if classname == "priest":
    addlist.append(discord.utils.get(channel.guild.roles, name="Priest"))
  else:
    removelist.append(discord.utils.get(channel.guild.roles, name="Priest"))
  if classname == "rogue":
    addlist.append(discord.utils.get(channel.guild.roles, name="Rogue"))
  else:
    removelist.append(discord.utils.get(channel.guild.roles, name="Rogue"))
  if classname == "shaman":
    addlist.append(discord.utils.get(channel.guild.roles, name="Shaman"))
  else:
    removelist.append(discord.utils.get(channel.guild.roles, name="Shaman"))
  if classname == "paladin":
    addlist.append(discord.utils.get(channel.guild.roles, name="Paladin"))
  else:
    removelist.append(discord.utils.get(channel.guild.roles, name="Paladin"))
  for add in addlist:
    await author.add_roles(add) 
  for remove in removelist:
    await author.remove_roles(remove) 
  await channel.send(name + " is now a " + classname + "!")

async def classlist(channel, client):
  members=client.get_all_members()
  classmap = {}
  classmap["Druid"] = 0
  classmap["Hunter"] = 0
  classmap["Mage"] = 0
  classmap["Paladin"] = 0
  classmap["Priest"] = 0
  classmap["Rogue"] = 0
  classmap["Shaman"] = 0
  classmap["Warlock"] = 0
  classmap["Warrior"] = 0
  classmap["Undecided"] = 0
  for member in members:
    #dont care about bot
    if not client.user.id == member.id:
      classes=0
      roles = member.roles
      if discord.utils.get(channel.guild.roles, name="Warrior") in roles:
        classmap["Warrior"]+= 1
        classes+= 1
      if discord.utils.get(channel.guild.roles, name="Druid") in roles:
        classmap["Druid"]+= 1
        classes+= 1
      if discord.utils.get(channel.guild.roles, name="Mage") in roles:
        classmap["Mage"]+= 1
        classes+= 1
      if discord.utils.get(channel.guild.roles, name="Warlock") in roles:
        classmap["Warlock"]+= 1
        classes+= 1
      if discord.utils.get(channel.guild.roles, name="Hunter") in roles:
        classmap["Hunter"]+= 1
        classes+= 1
      if discord.utils.get(channel.guild.roles, name="Priest") in roles:
        classmap["Priest"]+= 1
        classes+= 1
      if discord.utils.get(channel.guild.roles, name="Rogue") in roles:
        classmap["Rogue"]+= 1
        classes+= 1
      if discord.utils.get(channel.guild.roles, name="Shaman") in roles:
        classmap["Shaman"]+= 1
        classes+= 1
      if discord.utils.get(channel.guild.roles, name="Paladin") in roles:
        classmap["Paladin"]+= 1
        classes+= 1
      if classes > 1:
        await channel.send(member.name + " has multiple classes!")
      if classes == 0:
        classmap["Undecided"]+= 1

  message = ""
  for classname,count in classmap.items():
    message += classname + ": " + str(count) + "\n"

  embedMessage = discord.Embed()
  embedMessage.add_field(name="Classes", value=message)
  await channel.send(embed=embedMessage)

async def notEnoughArguments(channel, argsExpected, commandText):
  await channel.send(commandText + " requires at least " + str(argsExpected) + " argument" + ("s." if argsExpected > 1 else "."))

async def adddkp(channel,author,name,tokens,client):
  idlist = []
  amount = tokens[len(tokens)-1]
  intamount = 0
  members = list(client.get_all_members())
  #all but last are users to add dkp to
  for i in range(1,len(tokens) - 1):
    found = False
    currenttoken = tokens[i]
    if len(currenttoken) == 0:
      await channel.send("The empty string was found in the place of user " + str(i));
      return False
    record = sqldb.get_player_by_char_name(currenttoken)
    if record is not None and record:
      idlist.append(record[1])
      found = True
      continue
    #find member
    foundMember = None
    for member in members:
      if member.display_name == currenttoken:
        foundMember = member
        break
    if foundMember is not None:
      idlist.append(foundMember.id)
      found = True
      continue
    if not found:
      await channel.send("\"" +  currenttoken + "\"" + " is not a valid account.")
      return False
  
  #Check if dkp is a valid number
  if amount.isdigit() and int(amount) > 0:
    intamount = int(amount)
  else :
    await channel.send(amount + " is not a valid amount.")
    return False

  #now add that dkp!
  for d_id in idlist:
    sqldb.increment_dkp(d_id,amount)

  await channel.send(amount + " dkp has been added to given users!")
    

async def removedkp(channel,author,name,tokens,client):
  idlist = []
  amount = tokens[len(tokens)-1]
  intamount = 0
  members = list(client.get_all_members())
  #all but last are users to add dkp to
  for i in range(1,len(tokens) - 1):
    found = False
    currenttoken = tokens[i]
    if len(currenttoken) == 0:
      await channel.send("The empty string was found in the place of user " + str(i));
      return False
    record = sqldb.get_player_by_char_name(currenttoken)
    if record is not None and record:
      idlist.append(record[1])
      found = True
      continue
    #find member
    foundMember = None
    for member in members:
      if member.display_name == currenttoken:
        foundMember = member
        break
    if foundMember is not None:
      idlist.append(foundMember.id)
      found = True
      continue
    if not found:
      await channel.send("\"" +  currenttoken + "\"" + " is not a valid account.")
      return False
  
  #Check if dkp is a valid number
  if amount.isdigit() and int(amount) > 0:
    intamount = int(amount)
  else :
    await channel.send(amount + " is not a valid amount.")
    return False

  #now decremetn that dkp!
  for d_id in idlist:
    sqldb.decrement_dkp(d_id,amount)

  await channel.send(amount + " dkp has been removed from given users!")
 
async def bid(channel,author,name,tokens):
  global auction_mode
  global auction_item
  global auction_dict
  if not auction_mode:
    await channel.send("There is no auction currently running.")
    return False
  amount = tokens[1]
  if amount.isdigit() and int(amount) > 0:
    amount = int(amount)
  else :
    await channel.send(amount + " is not a valid amount.")
    return False
  #verify user has enough dkp
  currentdkp = sqldb.get_dkp(author.id)
  if amount > currentdkp:
    await channel.send("You do not have enough dkp to bid " + str(amount) + ". You currently have " + str(currentdkp) + "dkp.")
    return False
  auction_dict[author.id] = amount
  await channel.send("You have successfully bid " + str(amount) + " on " + auction_item + "!")
  

async def startauction(channel,name,tokens):
  global auction_mode
  global auction_item
  global auction_dict
  if auction_mode:
    await channel.send("There is already an auction running for " + auction_item + ". So wait for that to finish before starting another auction")
    return False
  sep = " "
  auction_item = sep.join(tokens[1:])
  auction_dict = {}
  auction_mode = True
  await channel.send("An auction has been started for " + auction_item + "! Send me a private message in the form \"!bid [amount]\" to bid.")

async def endauction(channel,name,client):
  global auction_mode
  global auction_item
  global auction_dict
  if not auction_mode:
    await channel.send("There is no auction currently running.")
    return False
  auction_mode = False
  message = ""
  sorted_dict = sorted(auction_dict.items(), key=operator.itemgetter(1), reverse=True)
  for uid,dkp in sorted_dict:
    member = channel.guild.get_member(uid)
    message += member.display_name + ": " + str(dkp) + "\n"
  
  embedMessage = discord.Embed()
  embedMessage.add_field(name="Auction for " + auction_item, value=message)
  await channel.send(embed=embedMessage)

async def item(channel,tokens):
  try:
    div = " "
    item_name = div.join(tokens[1:])
    oser = OpenSearch('item', item_name)
    oser.search_results.get_tooltip_data()
    image = oser.search_results.image
    await channel.send(file=discord.File(image))
    os.remove(image)
  except (OpenSearchError, SearchObjectError) as e:
    await channel.send(e)

async def spell(channel,tokens):
  try:
    div = " "
    spell_name = div.join(tokens[1:])
    oser = OpenSearch('spell', spell_name)
    oser.search_results.get_tooltip_data()
    image = oser.search_results.image
    await channel.send(file=discord.File(image))
    os.remove(image)
  except (OpenSearchError, SearchObjectError) as e:
    await channel.send(e)

async def setprof1(channel, author, name, prof):
  prof = prof.lower()
  if prof_map.get(prof) is None:
    await channel.send(prof + " is not a valid profession name.")
  else:
    prof1 = prof_map.get(prof)
    sqldb.set_prof1(author.id,prof1)
    await channel.send(name + " has added " + prof + " as prof1.")

async def setprof2(channel, author, name, prof):
  prof = prof.lower()
  if prof_map.get(prof) is None:
    await channel.send(prof + " is not a valid profession name.")
  else:
    prof2 = prof_map.get(prof)
    sqldb.set_prof2(author.id,prof2)
    await channel.send(name + " has added " + prof + " as prof2.")

async def getprofs(channel, author, name):
  prof1 = "None"
  prof1_temp = sqldb.get_prof1(author.id)
  prof2 = "None"
  prof2_temp = sqldb.get_prof2(author.id)
  if not prof1_temp is None:
    if inv_prof_map.get(prof1_temp) is None:
      prof1 = "None"
    else:
      prof1 = inv_prof_map.get(prof1_temp)
  if not prof2_temp is None:
    if inv_prof_map.get(prof2_temp) is None:
      prof2 = "None"
    else:
      prof2 = inv_prof_map.get(prof2_temp)
  await channel.send(name + " has the following profs: " + prof1 + " and " + prof2)

async def addrole(channel, author, name, role):
  role = role.lower()
  if role == "dps":
    await author.add_roles(discord.utils.get(channel.guild.roles, name="DPS")) 
    await channel.send(name + " is now a " + role + "!")
  elif role == "heal" or role == "healer":
    await author.add_roles(discord.utils.get(channel.guild.roles, name="HEALER")) 
    await channel.send(name + " is now a " + role + "!")
  elif role == "tank":
    await author.add_roles(discord.utils.get(channel.guild.roles, name="TANK")) 
    await channel.send(name + " is now a " + role + "!")
  else:
    await channel.send(role + " is not a valid role!")

async def removerole(channel, author, name, role):
  role = role.lower()
  if role == "dps":
    await author.remove_roles(discord.utils.get(channel.guild.roles, name="DPS")) 
    await channel.send(name + " is no longer a " + role + "!")
  elif role == "heal" or role == "healer":
    await author.remove_roles(discord.utils.get(channel.guild.roles, name="HEALER")) 
    await channel.send(name + " is no longer a " + role + "!")
  elif role == "tank":
    await author.remove_roles(discord.utils.get(channel.guild.roles, name="TANK")) 
    await channel.send(name + " is no longer a " + role + "!")
  else:
    await channel.send(role + " is not a valid role!")

async def days(channel, author, name):
  days = str(days_since_join(get_join_date(author.id)))
  await channel.send(name + " has been a member of the guild for " + days + " days!")

async def createevent(channel, tokens):
  start_time = None
  try:
    start_time = datetime.datetime.strptime(tokens[1], "%m/%d/%y-%H:%M")
  except ValueError:
    await channel.send(tokens[1] + " is not a valid date in the format \"%m/%d/%y-%H:%M\" - 05/28/99-16:40.")
    return
  duration = None
  if tokens[2].isdigit():
    duration = int(tokens[2])
  else: 
    await channel.send(tokens[2] + " is not a valid duration.")
    return
  event_type = tokens[3].lower()
  valid_types = ["casual", "raid", "pvp", "pve", "tournament"]
  if not event_type in valid_types:
    await channel.send(tokens[3] + " is not a valid type, the types are: ", str(valid_types))
    return
  dkp_amount = None
  if tokens[4].isdigit():
    dkp_amount = int(tokens[4])
  else: 
    await channel.send(tokens[4] + " is not a valid dkp amount")
    return
  
  name = tokens[5]
  description = " ".join(tokens[6:])

  #TODO add to database
  
  await channel.send("The event of type, " + event_type + ", named: " + name + ", " + description
      + " has been created to occur on " + str(start_time)
      + " and will run for " + str(duration) + " hours. Attendants will be awarded "
      + str(dkp_amount) + " dkp.")

async def removeevent(channel, tokens):
  event_id = None
  if tokens[1].isdigit():
    event_id = int(tokens[1])
  else: 
    await channel.send(str(tokens[1]) + " is not a valid id.")
    return

  #TODO add database hook
  await channel.send("The event with the id: " + str(event_id) + " has been removed.")

async def checkin(channel, author, name):
  #TODO logic
  title = "None"
  await channel.send(name + " has checked into the event titled: " + title)

async def forcecheckin(channel, author, tokens):
  #TODO logic
  player_id = tokens[1]
  discord_name = "N/A"
  title = "None"
  await channel.send(discord_name + " has been checked into the event titled: " + title)

async def didnotshow(channel, author, tokens):
  #TODO logic
  event_id = tokens[1]
  player_id = tokens[2]
  discord_name = "N/A"
  title = "None"
  await channel.send(discord_name + " has been removed from the event titled: " + title)


async def spenddkp(channel,author,name,tokens,client):
  await removedkp(channel,author,name,tokens,client)
  amount = 4999
  #TODO also add dkp from event pool
  await channel.send(str(amount) + " dkp has been added to the event pool!")

async def unspenddkp(channel,author,name,tokens,client):
  await adddkp(channel,author,name,tokens,client)
  amount = 4999
  #TODO also remove dkp from event pool
  await channel.send(str(amount) + " dkp has been removed from the event pool!")

async def startevent(channel, tokens):
  event_id = None
  if tokens[1].isdigit():
    event_id = int(tokens[1])
  else: 
    await channel.send(str(tokens[1]) + " is not a valid id.")
    return

  #TODO add database hook and end any other currently running events 
  await channel.send("The event with the id: " + str(event_id) + " has been begun!.")

async def endevent(channel):
  #TODO add database hook
  event_id = None
  await channel.send("The event with the id: " + str(event_id) + " has ended!")


async def addblacklist(channel,author,name,tokens,client):
  #TODO get username from token[1]
  userid = tokens[1]
  days = None
  if tokens[2].isdigit():
    days = int(tokens[2])
  else: 
    await channel.send(str(tokens[2]) + " is not a valid number of days")
    return
  offense = " ".join(tokens[3:])
  #TODO add database hook and run any other currently running events 
  event_id = None
  await channel.send("The user " + str(userid) + " has been added to the blacklist for " + str(days) + " days!")

async def removeblacklist(channel):
  #TODO add database hook
  blacklist_id = None
  await channel.send("The blacklist entry with the id: " + str(blacklist_id) + " has been removed!")

async def blacklist(channel):
  #TODO add database hook
  await channel.send("The following blacklist entries or whatever.")

async def parse_loot_master_commands(client,channel,author,name,content,roles,operation,tokens):
  if not discord.utils.get(channel.guild.roles, name="Loot Master") in roles:
    return False
  if operation == "adddkp":
    if len(tokens) >= 3:   
      await adddkp(channel,author,name,tokens,client)
    else:
      await notEnoughArguments(channel,2,"!adddkp")
    return True
  elif operation == "removedkp":
    if len(tokens) >= 3:   
      await removedkp(channel,author,name,tokens,client)
    else:
      await notEnoughArguments(channel,2,"!removedkp")
    return True
  if operation == "spenddkp":
    if len(tokens) >= 3:   
      await spenddkp(channel,author,name,tokens,client)
    else:
      await notEnoughArguments(channel,2,"!spenddkp")
    return True
  if operation == "unspenddkp":
    if len(tokens) >= 3:   
      await unspenddkp(channel,author,name,tokens,client)
    else:
      await notEnoughArguments(channel,2,"!unspenddkp")
    return True
  elif operation == "auction":
    if len(tokens) >= 2:   
      await startauction(channel,name,tokens)
    else:
      await notEnoughArguments(channel,1,"!auction")
    return True
  elif operation == "endauction":
    await endauction(channel,author,client)
    return True
  elif operation == "createevent":
    if len(tokens) >= 7:   
      await createevent(channel, tokens)
    else:
      await notEnoughArguments(channel,6,"!createevent")
    return True
  elif operation == "removeevent":
    if len(tokens) >= 2:   
      await removeevent(channel, tokens)
    else:
      await notEnoughArguments(channel,1,"!removeevent")
    return True
  elif operation == "startevent":
    if len(tokens) >= 2:   
      await startevent(channel, tokens)
    else:
      await notEnoughArguments(channel,1,"!startevent")
    return True
  elif operation == "endevent":
    await endevent(channel)
    return True

  return False

async def parse_loot_officer_commands(client,channel,author,name,content,roles,operation,tokens):
  if not discord.utils.get(channel.guild.roles, name="Captain Duck") in roles and not discord.utils.get(channel.guild.roles, name="Officer Duck") in roles:
    return False
  if operation == "forcecheckin":
    if len(tokens) >= 2:
      await forcecheckin(channel, author, tokens)
    else:
      await notEnoughArguments(channel,1,"!forcecheckin")
    return True
  if operation == "didnotshow":
    if len(tokens) >= 3:
      await didnotshow(channel, author, tokens)
    else:
      await notEnoughArguments(channel,2,"!didnotshow")
    return True
  if operation == "addblacklist":
    if len(tokens) >= 4:
      await addblacklist(channel,author,name,tokens,client)
    else:
      await notEnoughArguments(channel,3,"!addblacklist")
    return True
  if operation == "removeblacklist":
    if len(tokens) >= 2:
      await removeblacklist(channel)
    else:
      await notEnoughArguments(channel,1,"!removeblacklist")
    return True
  return False

async def parse_command(client,channel,author,name,content):
  if not content[0] == '!':
    return False
  #remove '!'
  message = content[1:]
  tokens = message.split()
  operation = tokens[0].lower()
  print(operation)
  if operation == "commands":
    await commands(channel)
  elif operation == "hello":
    await hello(channel, name)
  elif operation == "quack":
    await quack(channel, name)
  elif operation == "forthehorde":
    await forthehorde(channel, name)
  elif operation == "bid":
    await bid(channel,author,name,tokens)
  elif operation == "item":
    await item(channel,tokens)
  elif operation == "spell":
    await spell(channel,tokens)
  elif operation == "paladin" or operation == "pally":
    await paladin(channel)
  elif operation == "stats":
    await stats(channel, author, name)
  elif operation == "days":
    await days(channel, author, name)
  elif operation == "checkin":
    await checkin(channel, author, name)
  elif operation == "blacklist":
    await blacklist(channel)
  elif operation == "setname":
    if len(tokens) >= 2:   
      await setname(channel,author,name,tokens[1])
    else:
      await notEnoughArguments(channel,1,"!setname")
  elif operation == "setprof1":
    if len(tokens) == 2:   
      await setprof1(channel,author,name,tokens[1])
    else:
      await notEnoughArguments(channel,1,"!setprof1")
  elif operation == "setprof2":
    if len(tokens) == 2:   
      await setprof2(channel,author,name,tokens[1])
    else:
      await notEnoughArguments(channel,1,"!setprof2")
  elif operation == "getprofs":
    await getprofs(channel, author, name)
  elif operation == "addrole":
    if len(tokens) == 2:   
      await addrole(channel,author,name,tokens[1])
    else:
      await notEnoughArguments(channel,1,"!addrole")
  elif operation == "removerole":
    if len(tokens) == 2:   
      await removerole(channel,author,name,tokens[1])
    else:
      await notEnoughArguments(channel,1,"!removerole")
  elif type(channel) is discord.DMChannel:
    await channel.send("This command only works within a guild.")
  elif operation == "need":
    await need(channel, author, name)
  elif operation == "greed":
    await greed(channel, author, name)
  elif operation == "dkp":
    await dkp(channel, author, name)
  elif operation == "list":
    await listAcc(client,channel)
  elif operation == "countdown":
    await countdown(channel)
  elif operation == "setclass":
    if len(tokens) >= 2:   
      await setclass(channel,author,name,tokens[1],client)
    else:
      await notEnoughArguments(channel,1,"!setclass")
  elif operation == "classlist":
    await classlist(channel,client)
  elif await parse_loot_master_commands(client,channel,author,name,content,author.roles,operation,tokens):
    None #logic all in parse
  elif await parse_loot_officer_commands(client,channel,author,name,content,author.roles,operation,tokens):
    None #logic is done in parse
    
  


#verify tables exist
sqldb.init_db()
token = open(path+"/token", "r").readline()
print(token)
client = discord.Client()

@client.event
async def on_ready(): #This runs once when connected
  print(f'We have logged in as {client.user}')
  await client.change_presence(activity=discord.Game(name="Eat the Bread"))

@client.event
async def on_member_join(member):
  print("New user joined: " + member.display_name + str(member.id))
  add_player(member.id)
  channels = member.guild.channels
  await member.send("Welcome to the freshest pond in Azeroth, " + member.display_name + "!:duck:\n"
                    "Type !commands to see my list of commands.\n"
                    "Make sure to !setclass [classname] in guild chat to set your class and get appropriate coloring!")
  for channel in channels:
    if channel.name == "the-inn":
      await channel.send("Welcome to the freshest pond in Azeroth, " + member.display_name + "!:duck:")

@client.event
async def on_member_remove(member):
  print("User Left: " + member.display_name)
  set_status_abandoned(member.id)
  channels = member.guild.channels
  for channel in channels:
    if channel.name == "the-inn":
      await channel.send(member.display_name + " has flown south.")


@client.event
async def on_message(message):
  #Don't respond to self
  if not message.author == client.user:
    await parse_command(client,message.channel,message.author,message.author.display_name,message.content)
  print(f"{message.channel}: {message.author}: {message.author.name}: {message.content}")

client.run(token.strip())

