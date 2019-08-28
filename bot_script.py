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
import re
import math
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import glob

from open_search import OpenSearch, OpenSearchError, SearchObjectError
import sqldb

fpath=os.path.realpath(__file__)
path=os.path.dirname(fpath)
DB_FILE=path+"/local.db"
datetime_format = '%Y-%m-%d %H:%M:%S'
time_conversion_delta = datetime.timedelta(hours=3)

auction_mode = False
auction_item = ""
auction_dict = {}

def days_since_join(join_date):
  join = datetime.datetime.strptime(join_date,'%Y-%m-%d %H:%M:%S.%f')
  diff = datetime.datetime.now() - join
  days = diff.days
  return days

async def id_from_name(channel, client, name):
  members = list(client.get_all_members())

  #ret if empty
  if len(name) == 0:
    await channel.send("The empty string was found in the place of user " + name)
    return None

  #check if its a mention
  mention_id = re.search('\<\@[^0-9]*([^<>@!]+)\>', name)
  if mention_id is not None:
    disc_id = mention_id.group(1)
    if client.get_user(int(disc_id)) is not None:
      return disc_id
    else:
      await channel.send("An id was provided but its an invalid id: " + disc_id)
      return None

  #Now try by character name
  record = sqldb.get_player_by_char_name(name)
  if record is not None and record:
    return record[0]

  #find by discord name
  for member in members:
    if member.display_name == name:
      return member.id
  
  await channel.send("\"" +  name + "\"" + " is not a valid account.")
  return None

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


async def commands(channel, author, client):
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
            " - !blacklist - list current offense on the blacklist\n"
            " - !loot - lists the loot policy\n"
            " - !guildinfo - lists the hierarchy and officer positions\n"
          )
  events=(
          "These commands are to be used during events:\n"
          " - !checkin - check in to the current running event\n"
          " - !bid [amount] - bids an amount of dkp in the current auction - make sure to private message the bot for anonymity\n"
          " - !currentevent - displays information about the currently running event\n"
          " - !upcomingevents - displays information about all upcoming events\n"
          " - !checkedin - displays a list of all members checked in to the current event\n"
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
            " - !adddkp [user]... [amount] - adds amount of dkp to users - uses discord name or char name\n"
            " - !removedkp [user]... [amount] - removes amount of dkp from users in the event of fixing or punishment - uses discord name or char name\n"
            " - !auction [itemname] - starts an auction for [itemname] users my private message RoboDuck to bid\n"
            " - !uncheckin [event] [user] - Removes a checked in user from an event\n"
            " - !didshow [eventid] [name] - overrides didnotshow\n"
            )
  lootmaster_event=(
            "These commands are for controlling aspects of events:\n"
            " - !createevent [start time (Y-M-D-H:M) in EST time] [duration in hours] [type (casual, raid, pvp, pve, tournament)] [Min DKP Award] [name] [Description]\n"
            " - !removeevent [eventid] - Remove an event from the table\n"
            " - !startevent [eventid] - Start an event early, and end any other events currently running\n"
            " - !endevent - End the currently running event and distribute dkp\n"
            " - !spenddkp [user] [amount] - spend a users dkp for winning an auction - for keeping track of expenditures for null-value\n"
            " - !unspenddkp [user] [amount] - revert a mistake dkp spend for an auction\n"
            )
  moderation=(
            "These commands are for moderating players - Officers only:\n"
            " - !didnotshow [eventid] [name] - note that a checked in player did not show so they dont get points\n"
            " - !forcecheckin [name] - force check in a player if they are on the blacklist\n"
            " - !addblacklist [user] [days] [offense description] - Add a player to the blacklist to prevent them from checking into events and earning dkp\n"
            " - !removeblacklist [blacklist id] - Revmove an offense from the blacklist\n"
            " - !fullblacklist - Lists as much of the history of the blacklist as possible\n"
            )
  officer_character_modifications=(
            "If moderators notice something incorrect with a character, they can use these commands:\n"
            " - !forcesetprof1 [profession]- sets your first profession or none for no profession\n"
            " - !forcesetprof2 [profession]- sets your second profession or none for no profession\n"
            " - !forcesetname [name] - set the name of your character for armory lookups and other references\n"
            )


  embedMessage = discord.Embed()
  embedMessage.add_field(name="General Commands", value=message)
  embedMessage.add_field(name="Event Commands", value=events)
  embedMessage.add_field(name="Character Commands", value=character)
  if discord.utils.get(channel.guild.roles, name="Captain Duck") in author.roles or  discord.utils.get(channel.guild.roles, name="Officer Duck") in author.roles:
    embedMessage.add_field(name="Moderation Commands", value=moderation)
    embedMessage.add_field(name="Officer Character Modifications", value=officer_character_modifications)
  if discord.utils.get(channel.guild.roles, name="Loot Master") in author.roles:
    embedMessage.add_field(name="Loot Master Commands", value=lootmaster)
    embedMessage.add_field(name="Loot Master Event Commands", value=lootmaster_event)
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

async def guildinfo(channel):
  #make rich embed
  ranks=( 
          
          "**Captain Duck**: This role is reserved for the leaders of the guild @dj0wns and @Mesmer.\n"

          "**Officer Duck**: These are members who hold an officer role within the guild (current officer roles shown later in the post).\n"

          "**Elite Duck**: These are the more hardcore members of the guild who make it to every raid night or dominate in PVP.\n"

          "**Duck**: Core guild member, have passed the trial phase by being part of the guild for a few weeks.\n"

          "**Duckling**: New guild member, in a trial phase.\n\n"
         
          )
  filled_officer_positions=( 
          "**Raid Leader**(@Dj0wns currently - will take applications if you really want it): This officer's job is to coordinate the raid effort including explaining fights and general raid strategy.\n"

          "**Events Coordinator**(@Dj0wns currently): This officer's job is to host a weekly or bi-weekly guildwide event doing anything from dueling tournaments, to races across azeroth, to hide and seek or whatever you think would be fun. Going to these events would provide some amount of dkp so make them fun and worth attending!\n"

          "**Quartermaster**(@Saved): This officer's job is to make sure all the members of the guild are geared. They are the person who knows what is BiS and will help create or lead dungeon groups to get guild members BiS gear.\n\n"
          )
  open_officer_positions=( 
          "**PVP Leader**: This officer's job is to coordinate World PVP as well as be the shotcaller and strategist for groups of guild members in battlegrounds.\n"
          "**Recruitment Officer**: This officer's job is to recruit members to the guild. At first this will be to fill our initial raid roster and then continue to grow the guild.\n"

          "**Member Relations**: This officer's job is to make sure all the members of the guild are happy and to resolve conflicts. In the event of dissatisfaction with the guild among members, this officer's job is to advocate for the member experience among the rest of the officers to get the issue resolved.\n"
          )
  embedMessage = discord.Embed(color=0x8C1616)
  embedMessage.add_field(name="Ranks", value=ranks)
  embedMessage.add_field(name="Officer Positions", value=filled_officer_positions)
  embedMessage.add_field(name="Officer Positions Currently Open", value=open_officer_positions)
  await channel.send(embed=embedMessage)

async def loot(channel):
  #make rich embed
  distribute=( 
        "We will be prioritizing loot in the following fashion:\n"
        "1. If an item is BIS for the current content for our main tank it goes to our main tank. We need a strong main tank to progress deep into molten core so this helps everyone get more loot. The main tank will be tasked with creating and posting a planned BIS list for each set of content so that it is known which items will go to the tank. This includes mats for the crafted gear.\n"
        "2. Officers can reserve one item from each unique raid (one item in total for molten core, not each reset) and that will be publicized before we start doing the raid. This is to reward them for the extra work they put into making the guild function.\n"
        "3. The remaining items will be auctioned off using the DKP system.\n"
        "4. Anything that is not bid on will be disenchanted or sold and kept in the guild bank.\n"
          )
  dkp = (
      "DKP (Dragon kill points) are a looting system designed to fairly reward players for the time and effort they put into raids. You earn points from raids and other activities and get to spend those points on loot within raids.\n"
  )

  earn = (
      "DKP can be earned 2 different ways:\n"
      "Participating in Guild Raids: 10 DKP minimum per raid\n"
      "Participating in biweekly guild events: 5 DKP per event\n"
  )

  spend = (
      'When an item you want drops from a raid boss, a lootmaster will start a sealed auction where interested players can message RoboDuck "!bid [amount]" to bid on that item. Then the lootmaster will close the auction and reveal the bids. Whoever bid the highest gets the item. If there is a tie it will go to a roll between the top bidders. High roll wins the item and loses the DKP.\n'
      "There is a maximum bid of 100 DKP to prevent hoarding.\n"
  )

  null_value = (
        'To prevent inflation, when someone wins an item the DKP they bid will be split among all other members of the raid. So the better drops there are in a raid the better everyone gets paid. If less than 10 DKP is given to each player as the result of bids then each player will make a flat 10 DKP from participating in the raid.'
  )

  embedMessage = discord.Embed(color=0xa335ee)
  embedMessage.add_field(name="How We Distribute Loot", value=distribute)
  embedMessage.add_field(name="What is DKP?", value=dkp)
  embedMessage.add_field(name="How to Earn DKP", value=earn)
  embedMessage.add_field(name="How to Spend DKP", value=spend)
  embedMessage.add_field(name="How does Null-Value Work?", value=null_value)
  await channel.send(embed=embedMessage)

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
  main = (result[4] if not result[4] is None else "unknown")
  dkp = str(result[1])
  need= str(result[2])
  greed = str(result[3])
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
  results=sqldb.get_all_players()
  if results == None: return
  message = html_header()
  message += '<p style="font-size:40px">'
  for result in results:
    if not client.user.id == result[0]:
      user=channel.guild.get_member(result[0])
      #if user isnt in discord
      if user == None:
        continue
      message += (user.display_name + ":<br>" 
                 + (result[4] if not result[4] is None else "unknown")
                 + "&emsp;" + str(result[1]) + " dkp<br>" 
                 + "&emsp;" + str(result[2]) + " need rolls<br>"
                 + "&emsp;" + str(result[3]) + " greed rolls<br>")
  
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
  nametest = sqldb.get_player_by_char_name(accname)
  if nametest is None:
    sqldb.set_name(author.id,accname)
    await channel.send(name + "'s character name is now: " + accname)
  else:
    await channel.send("The character name, " + accname + ", is already in use.")
    

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
  #Check if dkp is a valid number
  idlist = []
  for i in range(1,len(tokens) - 1):
    d_id = await id_from_name(channel, client, tokens[i])
    if d_id is not None:
      idlist.append(d_id)
    else:
      return False

  amount = tokens[len(tokens)-1]
  if not amount.isdigit() or not int(amount) > 0:
    await channel.send(amount + " is not a valid amount.")
    return False

  #now add that dkp!
  for d_id in idlist:
    sqldb.increment_dkp(d_id,amount)

  await channel.send(amount + " dkp has been added to given users!")
    

async def removedkp(channel,author,name,tokens,client):
  #Check if dkp is a valid number
  idlist = []
  for i in range(1,len(tokens) - 1):
    d_id = await id_from_name(channel, client, tokens[i])
    if d_id is not None:
      idlist.append(d_id)
    else:
      return False

  amount = tokens[len(tokens)-1]
  if not amount.isdigit() or not int(amount) > 0:
    await channel.send(amount + " is not a valid amount.")
    return False

  #now decrement that dkp!
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
  prof_id = sqldb.get_prof_id(prof)
  if prof_id is not None:
    sqldb.set_prof1(author.id,prof_id)
    await channel.send(name + " has added " + prof + " as prof1.")
  else:
    await channel.send(prof + " is not a valid profession name.")

async def setprof2(channel, author, name, prof):
  prof_id = sqldb.get_prof_id(prof)
  if prof_id is not None:
    sqldb.set_prof2(author.id,prof_id)
    await channel.send(name + " has added " + prof + " as prof2.")
  else:
    await channel.send(prof + " is not a valid profession name.")

async def forcesetprof1(channel, client, tokens):
  d_id = await id_from_name(channel, client, tokens[1])
  if d_id is None:
    return False
  prof = tokens[2]
  prof_id = sqldb.get_prof_id(prof)
  if prof_id is not None:
    sqldb.set_prof1(d_id,prof_id)
    await channel.send(tokens[1] + " has added " + prof + " as prof1.")
  else:
    await channel.send(prof + " is not a valid profession name.")

async def forcesetprof2(channel, client, tokens):
  d_id = await id_from_name(channel, client, tokens[1])
  if d_id is None:
    return False
  prof = tokens[2]
  prof_id = sqldb.get_prof_id(prof)
  if prof_id is not None:
    sqldb.set_prof2(d_id,prof_id)
    await channel.send(tokens[1] + " has added " + prof + " as prof2.")
  else:
    await channel.send(prof + " is not a valid profession name.")

async def forcesetname(channel, client, tokens):
  d_id = await id_from_name(channel, client, tokens[1])
  if d_id is None:
    return False
  accname = tokens[2]
  nametest = sqldb.get_player_by_char_name(accname)
  if nametest is None:
    sqldb.set_name(d_id,accname)
    await channel.send(tokens[1] + "'s character name is now: " + accname)
  else:
    await channel.send("The character name, " + accname + ", is already in use.")

async def getprofs(channel, author, name):
  prof1 = sqldb.get_prof1(author.id)
  prof2 = sqldb.get_prof2(author.id)
  await channel.send(name + " has the following profs: " + prof1 + " and " + prof2)

async def addrole(channel, author, name, role):
  role = role.lower()
  if role == "dps":
    await author.add_roles(discord.utils.get(channel.guild.roles, name="DPS")) 
    await channel.send(name + " is now a " + role + "!")
  elif role == "heal" or role == "healer":
    await author.add_roles(discord.utils.get(channel.guild.roles, name="HEALER")) 
    await channel.send(name + " is now a healer!")
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
    await channel.send(name + " is no longer a healer!")
  elif role == "tank":
    await author.remove_roles(discord.utils.get(channel.guild.roles, name="TANK")) 
    await channel.send(name + " is no longer a " + role + "!")
  else:
    await channel.send(role + " is not a valid role!")

async def days(channel, author, name):
  days = str(days_since_join(sqldb.get_joined_at(author.id)))
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

  end_time = start_time + datetime.timedelta(hours=duration)

  sqldb.add_event(name,description,start_time,end_time,event_type,dkp_amount)

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

  if sqldb.get_event(event_id) is None:
    await channel.send("The event with the id: " + str(event_id) + " does not exist.")
  else:
    sqldb.remove_event(event_id)
    await channel.send("The event with the id: " + str(event_id) + " has been removed.")

async def checkin(channel, author, name):
  running_event = sqldb.get_current_event()
  if running_event is None:
    await channel.send("There is no event currently running.")
    return
  if sqldb.is_blacklisted(author.id) == 1 : 
    await channel.send("You are currently blacklisted from registering for events.")
    return
    
  await forcecheckin(channel, author, None, author.id)

async def forcecheckin(channel, author, token, player_id=None):
  running_event = sqldb.get_current_event()
  if running_event is None:
    await channel.send("There is no event currently running.")
    return
  if player_id is None:
    player_id = await id_from_name(channel, client, token)

  if player_id is None:
    await channel.send("No user with the name: " + token + " exists.")
    return

  user = client.get_user(int(player_id));
  
  sqldb.add_attendance(running_event[0],player_id)

  await channel.send(user.name + " has been checked in to the event titled: "  + running_event[1])

async def uncheckin(channel, author, tokens):
  running_event = sqldb.get_current_event()
  if running_event is None:
    await channel.send("There is no event currently running.")
    return
  player_id = await id_from_name(channel, client, tokens[1])

  if player_id is None:
    await channel.send("No user with the name: " + tokens[1] + " exists.")
    return

  user=channel.guild.get_member(int(player_id))
  
  sqldb.remove_attendance(running_event[0], player_id)

  await channel.send(user.display_name + " has been checked out of the event titled: "  + running_event[1])

async def didnotshow(channel, author, tokens):
  event_id = tokens[1]
  player_id = await id_from_name(channel, client, tokens[2])
  if tokens[1].isdigit():
    event_id = int(tokens[1])
  else: 
    await channel.send(str(tokens[1]) + " is not a valid id.")
    return

  if player_id is None:
    await channel.send("No user with the name: " + tokens[2] + " exists.")
    return

  if sqldb.is_checked_in(event_id, player_id) == 0:
    await channel.send("No user with the name: " + tokens[2] + " is checked in to the event: " + str(event_id))
    return
    

  sqldb.set_attended(event_id,player_id, 0)
  player = sqldb.get_player(player_id)
  user = client.get_user(int(player_id));
  name = user.name
  await channel.send(name + " has been marked did not show from the event titled: " + str(event_id))

async def didshow(channel, author, tokens):
  event_id = tokens[1]
  player_id = await id_from_name(channel, client, tokens[2])
  if tokens[1].isdigit():
    event_id = int(tokens[1])
  else: 
    await channel.send(str(tokens[1]) + " is not a valid id.")
    return

  if player_id is None:
    await channel.send("No user with the name: " + tokens[2] + " exists.")
    return

  if sqldb.is_checked_in(event_id, player_id) == 0:
    await channel.send("No user with the name: " + tokens[2] + " is checked in to the event: " + str(event_id))
    return
    

  sqldb.set_attended(event_id,player_id,1)
  player = sqldb.get_player(player_id)
  user = client.get_user(int(player_id));
  name = user.name
  await channel.send(name + " has been marked did show from the event titled: " + str(event_id))


async def spenddkp(channel,author,name,tokens,client):
  amount = None
  running_event = sqldb.get_current_event()
  if running_event is None:
    await channel.send("There is no event currently running.")
    return
  if not running_event[5] == "raid":
    await channel.send("The current running event is not a raid.")
    return
  player_id = await id_from_name(channel, client, tokens[1])
  if player_id is None:
    await channel.send("No user with the name: " + tokens[1] + " exists.")
    return
  if tokens[2].isdigit():
    amount = int(tokens[2])
  else: 
    await channel.send(str(tokens[2]) + " is not a valid dkp amount.")
    return
  event_id = running_event[0]
  if sqldb.is_checked_in(event_id, player_id) == 0:
    await channel.send("No user with the name: " + tokens[1] + " is checked in to the current running event.")
    return


  success = await removedkp(channel,author,name,tokens,client)
  if success == False:
    return False
  sqldb.set_dkp_spent(event_id, running_event[7] + amount)
  await channel.send(str(amount) + " dkp has been added to the event pool!")

async def unspenddkp(channel,author,name,tokens,client):
  amount = None
  running_event = sqldb.get_current_event()
  if running_event is None:
    await channel.send("There is no event currently running.")
    return
  if not running_event[5] == "raid":
    await channel.send("The current running event is not a raid.")
    return
  player_id = await id_from_name(channel, client, tokens[1])
  if player_id is None:
    await channel.send("No user with the name: " + tokens[1] + " exists.")
    return
  if tokens[2].isdigit():
    amount = int(tokens[2])
  else: 
    await channel.send(str(tokens[2]) + " is not a valid dkp amount.")
    return
  event_id = running_event[0]
  if sqldb.is_checked_in(event_id, player_id) == 0:
    await channel.send("No user with the name: " + tokens[1] + " is checked in to the current running event.")
    return


  success = await adddkp(channel,author,name,tokens,client)
  if success == False:
    return False
  sqldb.set_dkp_spent(event_id, running_event[7] - amount)
  await channel.send(str(amount) + " dkp has been removed from the event pool!")

async def event_begin_announcement(channel, client):
  #announcement channel

  channel = client.get_channel(581739109928927277)
  running_event = sqldb.get_current_event()
  if running_event is None:
    return
  name = running_event[1]
  description = running_event[2]
  event_type = running_event[5]
  dkp_amount = running_event[6]

  await channel.send("@everyone - " + name + " has begun! Attend and !checkin to earn DKP!")
  await currentevent(channel)

async def startevent(channel, client, tokens):
  event_id = None
  if tokens[1].isdigit():
    event_id = int(tokens[1])
  else: 
    await channel.send(str(tokens[1]) + " is not a valid id.")
    return
  
  event = sqldb.get_event(event_id)
  if event is None:
    await channel.send("The event with the id: " + str(event_id) + " does not exist.")
    return

  if event[8] == 1:
    await channel.send("The event with the id: " + str(event_id) + " has already begun.")
    return
    
  
  running_event = sqldb.get_current_event()
  if running_event is not None:
    await endevent(channel)

  sqldb.set_event_started(event_id)
  await event_begin_announcement(channel, client)
  await channel.send("The event with the id: " + str(event_id) + " has been begun!.")

async def endevent(channel):
  running_event = sqldb.get_current_event()
  if running_event is None:
    await channel.send("There is no event currently running.")
    return
  event_id = running_event[0]
  attendees = sqldb.get_attendees(event_id)
  attendee_len = len(attendees)
  if attendee_len < 1:
    attendee_len = 1
  dkp_base = running_event[6]
  dkp_spent = running_event[7]
  dkp_per_player = math.ceil(float(dkp_spent)/float(attendee_len))
  dkp_awarded = None
  if dkp_base > dkp_per_player:
    dkp_awarded = dkp_base
  else:
    dkp_awarded = dkp_per_player

  sqldb.set_event_finished(event_id)
  for player_id in attendees:
    #player_id is a tuple here
    sqldb.increment_dkp(player_id[0],dkp_awarded)

  await channel.send("The event with the id: " + str(event_id) + " has ended and " + str(dkp_awarded) + " dkp has been given to all attendees!")


async def addblacklist(channel,author,name,tokens,client):
  user_id = await id_from_name(channel, client, tokens[1])
  days = None
  if user_id is None:
    await channel.send("No user with the name: " + tokens[1] + " exists.")
    return
  if tokens[2].isdigit():
    days = int(tokens[2])
  else: 
    await channel.send(str(tokens[2]) + " is not a valid number of days")
    return
  offense = " ".join(tokens[3:])
  start_time = datetime.datetime.now()
  end_time = start_time + datetime.timedelta(days=days)
  sqldb.add_to_blacklist(user_id, start_time, end_time, name, offense)
  await channel.send("The user " + tokens[1] + " has been added to the blacklist for " + str(days) + " days!")

async def removeblacklist(channel, tokens):
  blacklist_id = tokens[1]
  if not blacklist_id.isdigit():
    await channel.send("The blacklist entry with the id: " + str(blacklist_id) + " does not exist!")
    return
  
  if sqldb.get_from_blacklist(blacklist_id) is None:
    await channel.send("The blacklist entry with the id: " + str(blacklist_id) + " does not exist!")
    return
  
  sqldb.remove_from_blacklist(blacklist_id)
  await channel.send("The blacklist entry with the id: " + str(blacklist_id) + " has been removed!")

async def blacklist(channel):
  blacklist = sqldb.get_blacklist(datetime.datetime.now())
  message = "Player   |   Start   |   End   |   Offense\n"
  for item in blacklist:
    player = sqldb.get_player(item[1])
    name = player[4]
    message += name + "   |   " + item[2] + "   |   " + item[3] + "   |   " + item[5] + "\n"

  embedMessage = discord.Embed()
  embedMessage.add_field(name="Current Blacklist", value=message)
  await channel.send(embed=embedMessage)

async def fullblacklist(channel):
  blacklist = sqldb.get_blacklist()
  message = "Player   |   Start   |   End   |   Offense\n"
  for item in blacklist:
    player = sqldb.get_player(item[1])
    name = player[4]
    if name is None:
      name = "Unknown"
    message += name + "   |   " + item[2] + "   |   " + item[3] + "   |   " + item[5] + "\n"

  embedMessage = discord.Embed()
  embedMessage.add_field(name="Full Blacklist", value=message)
  await channel.send(embed=embedMessage)

def event_to_embed(event):
  event_id = event[0]
  name = event[1]
  description = event[2]
  start_date = datetime.datetime.strptime(event[3], datetime_format)
  end_date = datetime.datetime.strptime(event[4], datetime_format)
  event_type = event[5]
  min_dkp_award = event[6]
  total_dkp_spent = event[7]

  start_date -= time_conversion_delta
  end_date -= time_conversion_delta

  start_time = start_date.strftime("%m/%d/%Y, %I:%M %p") + " PST"
  end_time = end_date.strftime("%m/%d/%Y, %I:%M %p") + " PST"

  #append id to description
  description += "\nEvent id: " + str(event_id)
  
  embedMessage = discord.Embed(title=name, description=description, color=0x091bff)
  embedMessage.add_field(name="Type", value=event_type, inline=True)
  embedMessage.add_field(name="Minimum DKP Award", value=str(min_dkp_award), inline=True)
  embedMessage.add_field(name="Current DKP Spent", value=str(total_dkp_spent), inline=True)
  embedMessage.add_field(name="Start Time", value=str(start_time), inline=True)
  embedMessage.add_field(name="End Time", value=str(end_time), inline=True)
  
  return embedMessage

async def currentevent(channel):
  running_event = sqldb.get_current_event()
  if running_event is None:
    await channel.send("There is no event currently running.")
    return
  
  embedMessage = event_to_embed(running_event)
  await channel.send(embed=embedMessage)
    
async def upcomingevents(channel):
  events = sqldb.get_upcoming_events()
  for event in events:
    embedMessage = event_to_embed(event)
    await channel.send(embed=embedMessage)

async def checkedin(channel):
  running_event = sqldb.get_current_event()
  if running_event is None:
    await channel.send("There is no event currently running.")
    return
  attendees = sqldb.get_attendees(running_event[0])
  if attendees is None:
    await channel.send("There is no one checked in.")
    return
  message = ""
  embedMessage = discord.Embed(title=running_event[1])
  for attendee in attendees:
    player_id = attendee[0]
    player = sqldb.get_player(player_id)
    name = player[4]
    if name is None:
      name = "Unknown"
    user = client.get_user(int(player_id));
    discord_name = user.name
    if len(message) > 1000:
      embedMessage.add_field(name="Checked In",value=message)
      message = ""
    message += discord_name + "   |   " + name + "\n";
      
  embedMessage.add_field(name="Checked In",value=message)
  await channel.send(embed=embedMessage)



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
      await startevent(channel, client, tokens)
    else:
      await notEnoughArguments(channel,1,"!startevent")
    return True
  elif operation == "endevent":
    await endevent(channel)
    return True
  elif operation == "uncheckin":
    if len(tokens) >= 2:
      await uncheckin(channel, author, tokens)
    else:
      await notEnoughArguments(channel,1,"!uncheckin")
    return True
  elif operation == "didshow":
    if len(tokens) >= 3:
      await didshow(channel, author, tokens)
    else:
      await notEnoughArguments(channel,2,"!didshow")
    return True

  return False

async def parse_loot_officer_commands(client,channel,author,name,content,roles,operation,tokens):
  if not discord.utils.get(channel.guild.roles, name="Captain Duck") in roles and not discord.utils.get(channel.guild.roles, name="Officer Duck") in roles:
    return False
  if operation == "forcecheckin":
    if len(tokens) >= 2:
      await forcecheckin(channel, author, tokens[1])
    else:
      await notEnoughArguments(channel,1,"!forcecheckin")
    return True
  elif operation == "didnotshow":
    if len(tokens) >= 3:
      await didnotshow(channel, author, tokens)
    else:
      await notEnoughArguments(channel,2,"!didnotshow")
    return True
  elif operation == "addblacklist":
    if len(tokens) >= 4:
      await addblacklist(channel,author,name,tokens,client)
    else:
      await notEnoughArguments(channel,3,"!addblacklist")
    return True
  elif operation == "removeblacklist":
    if len(tokens) >= 2:
      await removeblacklist(channel, tokens)
    else:
      await notEnoughArguments(channel,1,"!removeblacklist")
    return True
  elif operation == "fullblacklist":
    await fullblacklist(channel)
    return True
  elif operation == "forcesetprof1":
    if len(tokens) == 3:   
      await forcesetprof1(channel,client,tokens)
    else:
      await notEnoughArguments(channel,2,"!forcesetprof1")
  elif operation == "forcesetprof2":
    if len(tokens) == 3:   
      await forcesetprof2(channel,client,tokens)
    else:
      await notEnoughArguments(channel,3,"!forcesetprof2")
  elif operation == "forcesetname":
    if len(tokens) == 3:   
      await forcesetname(channel,client,tokens)
    else:
      await notEnoughArguments(channel,3,"!forcesetname")
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
    await commands(channel,author,client)
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
  elif operation == "checkedin":
    await checkedin(channel)
  elif operation == "blacklist":
    await blacklist(channel)
  elif operation == "currentevent":
    await currentevent(channel)
  elif operation == "upcomingevents":
    await upcomingevents(channel)
  elif operation == "loot":
    await loot(channel)
  elif operation == "guildinfo":
    await guildinfo(channel)
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

  while True:
    event = sqldb.get_next_event()
    if event is not None:
      event_start = datetime.datetime.strptime(event[3], datetime_format)
      print(str(event_start) + " " +  str(datetime.datetime.now()))
      if event_start <=  datetime.datetime.now():
        #announce in the Inn
        channel = client.get_channel(581612148837449730)
        event_id = event[0]
        tokens = [None]
        tokens.append(str(event_id))
        await startevent(channel, client, tokens)
        
    await asyncio.sleep(30) #Waits for 10 seconds

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
    try:
      if len(message.content) > 0:
        await parse_command(client,message.channel,message.author,message.author.display_name,message.content)
    except Exception as e:
      print(e)
      await message.channel.send("Exception raised: '" + str(e) + "'\n - Pester dj0wns that his bot is broken on this command")
      
  print(f"{message.channel}: {message.author}: {message.author.name}: {message.content}")

client.run(token.strip())

