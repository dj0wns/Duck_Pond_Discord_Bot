import sqlite3
import discord
import asyncio
import random
import os
import datetime
import imgkit
import tempfile
import io
from sqlite3 import Error

fpath=os.path.realpath(__file__)
path=os.path.dirname(fpath)
DB_FILE=path+"/local.db"

def create_table(conn):
  sql_create_players_table = """ CREATE TABLE IF NOT EXISTS players (
                                    id integer PRIMARY KEY,
                                    discord_id integer NOT NULL,
                                    dkp integer,
                                    need_rolls integer,
                                    greed_rolls integer,
                                    account_name text
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
  sql = '''INSERT INTO players(discord_id,dkp,need_rolls,greed_rolls,account_name)
           VALUES(?,?,?,?,?)  '''
  to_insert = (discord_id,0,0,0,"")
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

def get_account_record(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    if not check_player_table(conn): return None
    create_account_if_doesnt_exist(conn, discord_id)
    cur = conn.cursor()
    cur.execute("SELECT * FROM players WHERE discord_id=" + str(discord_id))
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
            "!commands - displays this helpful dialogue\n"
            "!need - rolls need from 0-100\n"
            "!greed - rolls greed from 0-100\n"
            "!list - lists dkp totals of all members\n"
            "!dkp - returns how much dkp you have\n"
            "!stats - prints your stats sheet\n"
            "!countdown - returns how much time till classic release\n"
            "!setname [name] - set the name of your character for armory lookups and other references\n"
            "!setclass [class] - set your primary class\n"
            "!classlist - list the number of each class currently in the guild\n"
          )

  embedMessage = discord.Embed()
  embedMessage.add_field(name="Commands", value=message)
  await channel.send(embed=embedMessage)

async def hello(channel, name):
  await channel.send('Hi ' + name + "!")

async def quack(channel, name):
  await channel.send('Quack!')

async def need(channel, author, name):
  increment_need(author.id)
  await channel.send(name + " need rolled a " + str(random_num()) + "!")

async def greed(channel, author, name):
  increment_greed(author.id)
  await channel.send(name + " greed rolled a " + str(random_num()) + "!")

async def dkp(channel, author, name):
  await channel.send(name + " you have " + str(get_dkp(author.id)) + " dkp!")

async def stats(channel, author, name):
  result = get_account_record(author.id)
  message = html_header()
  message += ('<p style="font-size:40px">' + name + "'s main is: " + (result[5] if not result[5] == "" else "unknown")
             + "\t|\t" + str(result[2]) + " dkp" 
             + "\t|\t" + str(result[3]) + " n "
             + "\t|\t" + str(result[4]) + " g.\n")
  message += html_footer()
  await send_html(channel,message)

async def listAcc(client,channel):
  #make sure all members are accounted for
  members=client.get_all_members()
  for member in members:
    #dont add self
    if not client.user.id == member.id:
      add_account_record(member.id)
  
  results=print_account_records()
  message = ""
  for result in results:
    if not client.user.id == result[1]:
      user=channel.guild.get_member(result[1])
      message += (user.display_name + "'s main is: " + (result[5] if not result[5] == "" else "unknown")
                 + "\t|\t" + str(result[2]) + " dkp" 
                 + "\t|\t" + str(result[3]) + " n "
                 + "\t|\t" + str(result[4]) + " g.\n")
  
  embedMessage = discord.Embed()
  embedMessage.add_field(name="Ducks", value=message)
  
  await channel.send(embed=embedMessage)

async def countdown(channel):
  release = datetime.datetime(2019, 8, 26)
  current = datetime.datetime.now()
  togo = release - current
  await channel.send("There are only " + str(togo.days) + " days until classic is released!")

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

async def parse_command(client,channel,author,name,content):
  if not content[0] == '!':
    return False
  #remove '!'
  message = content[1:]
  tokens = message.split(" ")
  operation = tokens[0].lower()
  print(operation)
  if operation == "commands":
    await commands(channel)
  elif operation == "hello":
    await hello(channel, name)
  elif operation == "quack":
    await quack(channel, name)
  elif operation == "need":
    await need(channel, author, name)
  elif operation == "greed":
    await greed(channel, author, name)
  elif operation == "dkp":
    await dkp(channel, author, name)
  elif operation == "stats":
    await stats(channel, author, name)
  elif operation == "list":
    await listAcc(client,channel)
  elif operation == "countdown":
    await countdown(channel)
  elif operation == "setname":
    if len(tokens) >= 2:   
      await setname(channel,author,name,tokens[1])
    else:
      await notEnoughArguments(channel,1,"!setname")
  elif operation == "setclass":
    if len(tokens) >= 2:   
      await setclass(channel,author,name,tokens[1],client)
    else:
      await notEnoughArguments(channel,1,"!setclass")
  elif operation == "classlist":
      await classlist(channel,client)
    
  

token = open(path+"/token", "r").readline()
print(token)
client = discord.Client()

@client.event
async def on_ready(): #This runs once when connected
  print(f'We have logged in as {client.user}')
  await client.change_presence(activity=discord.Game(name="Eat the Bread"))

@client.event
async def on_message(message):
  #Don't respond to self
  if not message.author == client.user:
    await parse_command(client,message.channel,message.author,message.author.display_name,message.content)
  print(f"{message.channel}: {message.author}: {message.author.name}: {message.content}")

client.run(token.strip())

