import sqlite3
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
from sqlite3 import Error
from open_search import OpenSearch, OpenSearchError, SearchObjectError

fpath=os.path.realpath(__file__)
path=os.path.dirname(fpath)
DB_FILE=path+"/local.db"

auction_mode = False
auction_item = ""
auction_dict = {}

def create_table(conn):
  sql_create_players_table = """ CREATE TABLE IF NOT EXISTS players (
                                    id integer PRIMARY KEY,
                                    discord_id integer NOT NULL,
                                    dkp integer,
                                    need_rolls integer,
                                    greed_rolls integer,
                                    account_name text,
                                    join_date datetime
                                ); """
  try:
    c = conn.cursor()
    c.execute(sql_create_players_table)
  except Error as e:
    print(e)

def create_account_if_doesnt_exist(conn, discord_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM players WHERE discord_id=" + str(discord_id))
    #if element doesnt exist create it
    if cur.fetchone() == None:
      create_player(conn, discord_id)


def create_player(conn, discord_id):
  sql = '''INSERT INTO players(discord_id,dkp,need_rolls,greed_rolls,account_name,join_date)
           VALUES(?,?,?,?,?,?)  '''
  to_insert = (discord_id,0,0,0,"",str(datetime.datetime.now()))
  try:
    cur = conn.cursor()
    cur.execute(sql, to_insert)
    conn.commit()
    #else do nothing
  except Error as e:
    print(e)

def check_player_table(conn):
  if conn is not None:
    create_table(conn)
    return True
  else:
    print("Error, database connection is null")
    return False


def add_account_record(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    if not check_player_table(conn): return None
    create_account_if_doesnt_exist(conn, discord_id)
  except Error as e:
    print(e)
  finally:
    conn.close()

def remove_account_record(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    if not check_player_table(conn): return None
    cur = conn.cursor()
    cur.execute("DELETE FROM players WHERE discord_id=" + str(discord_id))
    conn.commit()
  except Error as e:
    print(e)
  finally:
    conn.close()

def get_account_record(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    if not check_player_table(conn): return None
    create_account_if_doesnt_exist(conn, discord_id)
    cur = conn.cursor()
    cur.execute("SELECT * FROM players WHERE discord_id=" + str(discord_id) )
    result = cur.fetchone()
    return result
  except Error as e:
    print(e)
  finally:
    conn.close()

def get_account_record_by_acc_name(account_name):
  try:
    conn = sqlite3.connect(DB_FILE)
    if not check_player_table(conn): return None
    cur = conn.cursor()
    cur.execute("SELECT * FROM players WHERE account_name=?",(account_name,))
    result = cur.fetchone()
    return result
  except Error as e:
    print(e)
  finally:
    conn.close()

def print_account_records():
  try:
    conn = sqlite3.connect(DB_FILE)
    if not check_player_table(conn): return None
    cur = conn.cursor()
    cur.execute("SELECT * FROM players")
    results = cur.fetchall()
    return results
  except Error as e:
    print(e)
  finally:
    conn.close()

def increment_dkp(discord_id, amount):
  try:
    conn = sqlite3.connect(DB_FILE)
    if not check_player_table(conn): return None
    create_account_if_doesnt_exist(conn, discord_id)
    cur = conn.cursor()
    cur.execute("UPDATE players SET dkp = dkp + " + str(amount) + " WHERE discord_id=" + str(discord_id))
    conn.commit()
  except Error as e:
    print(e)
  finally:
    conn.close()

def decrement_dkp(discord_id, amount):
  try:
    conn = sqlite3.connect(DB_FILE)
    if not check_player_table(conn): return None
    create_account_if_doesnt_exist(conn, discord_id)
    cur = conn.cursor()
    cur.execute("UPDATE players SET dkp = MAX(dkp - " + str(amount) + " , 0) WHERE discord_id=" + str(discord_id))
    conn.commit()
  except Error as e:
    print(e)
  finally:
    conn.close()

def get_dkp(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    if not check_player_table(conn): return None
    create_account_if_doesnt_exist(conn, discord_id)
    cur = conn.cursor()
    cur.execute("SELECT dkp FROM players WHERE discord_id=" + str(discord_id))
    return cur.fetchone()[0]
  except Error as e:
    print(e)
  finally:
    conn.close()

def increment_need(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    if not check_player_table(conn): return None
    create_account_if_doesnt_exist(conn, discord_id)
    cur = conn.cursor()
    cur.execute("UPDATE players SET need_rolls = need_rolls + 1 WHERE discord_id=" + str(discord_id))
    conn.commit()
  except Error as e:
    print(e)
  finally:
    conn.close()

def increment_greed(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    if not check_player_table(conn): return None
    create_account_if_doesnt_exist(conn, discord_id)
    cur = conn.cursor()
    cur.execute("UPDATE players SET greed_rolls = greed_rolls + 1 WHERE discord_id=" + str(discord_id))
    conn.commit()
  except Error as e:
    print(e)
  finally:
    conn.close()

def set_name(discord_id, name):
  try:
    conn = sqlite3.connect(DB_FILE)
    if not check_player_table(conn): return None
    create_account_if_doesnt_exist(conn, discord_id)
    cur = conn.cursor()
    #the parens sanitize input i guess
    cur.execute("UPDATE players SET account_name=? WHERE discord_id=" + str(discord_id), (name,))
    conn.commit()
  except Error as e:
    print(e)
  finally:
    conn.close()

def get_join_date(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    if not check_player_table(conn): return None
    create_account_if_doesnt_exist(conn, discord_id)
    cur = conn.cursor()
    cur.execute("SELECT join_date FROM players WHERE discord_id=" + str(discord_id))
    return cur.fetchone()[0]
  except Error as e:
    print(e)
  finally:
    conn.close()

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
            "!hello - says hello back!\n"
            "!quack - Quacks!\n"
            "!forthehorde - The alliance will tremble beneath these fearsome warcries!\n"
            "!commands - displays this helpful dialogue\n"
            "!item [itemname] - if exists, returns an infobox detailing the named item\n"
            "!spell [spellname] - if exists, returns an infobox detailing the named spell\n"
            "!need - rolls need from 0-100\n"
            "!greed - rolls greed from 0-100\n"
            "!list - lists dkp totals of all members\n"
            "!dkp - returns how much dkp you have\n"
            "!stats - prints your stats sheet\n"
            "!countdown - returns how much time till classic release\n"
            "!paladin - asserts your role as a horde paladin\n"
            "!setname [name] - set the name of your character for armory lookups and other references\n"
            "!setclass [class] - set your primary class\n"
            "!classlist - list the number of each class currently in the guild\n"
            "!bid [amount] - bids an amount of dkp in the current auction - make sure to private message the bot for anonymity\n"
          )
  
  lootmaster=( 
            "These commands only work if you have the \"Loot Master\" role.\n"
            "!adddkp [user]... [amount] - adds amount of dkp to users - uses discord name or char name\n"
            "!adddkp [user]... [amount] - removes amount of dkp from users - uses discord name or char name\n"
            "!auction [itemname] - starts an auction for [itemname] users my private message RoboDuck to bid\n"
             )

  embedMessage = discord.Embed()
  embedMessage.add_field(name="General Commands", value=message)
  embedMessage.add_field(name="Loot Master", value=lootmaster)
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
  increment_need(author.id)
  await channel.send(name + " need rolled a " + str(random_num()) + "!")

async def greed(channel, author, name):
  increment_greed(author.id)
  await channel.send(name + " greed rolled a " + str(random_num()) + "!")

async def dkp(channel, author, name):
  await channel.send(name + " you have " + str(get_dkp(author.id)) + " dkp!")

async def paladin(channel):
  await channel.send(file=discord.File(path + "/paladin.png","paladin.png"))

async def stats(channel, author, name):
  result = get_account_record(author.id)
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
  members=client.get_all_members()
  for member in members:
    #dont add self
    if not client.user.id == member.id:
      add_account_record(member.id)
  
  results=print_account_records()
  if results == None: return
  message = html_header()
  message += '<p style="font-size:40px">'
  for result in results:
    if not client.user.id == result[1]:
      user=channel.guild.get_member(result[1])
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
  set_name(author.id,accname)
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
    record = get_account_record_by_acc_name(currenttoken)
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
    increment_dkp(d_id,amount)

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
    record = get_account_record_by_acc_name(currenttoken)
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
    decrement_dkp(d_id,amount)

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
  currentdkp = get_dkp(author.id)
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
  elif operation == "auction":
    if len(tokens) >= 2:   
      await startauction(channel,name,tokens)
    else:
      await notEnoughArguments(channel,1,"!auction")
    return True
  elif operation == "endauction":
    await endauction(channel,author,client)
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
  elif operation == "setname":
    if len(tokens) >= 2:   
      await setname(channel,author,name,tokens[1])
    else:
      await notEnoughArguments(channel,1,"!setname")
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
    None #logic is done in parse
    
  

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
  add_account_record(member.id)
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
  remove_account_record(member.id)
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

