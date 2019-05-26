import sqlite3
import discord
import asyncio
import random
import os
import datetime
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


def random_num():
  return random.randint(0,100)

async def commands(channel):
  message=( "```"
            "!hello - says hello back!\n"
            "!commands - displays this helpful dialogue\n"
            "!need - rolls need from 0-100\n"
            "!greed - rolls greed from 0-100\n"
            "!list - lists dkp totals of all members\n"
            "!dkp - returns how much dkp you have\n"
            "!countdown - returns how much time till classic release\n"
            "```"
          )
  await channel.send(message)

async def hello(channel, name):
  await channel.send('Hi ' + name + "!")

async def need(channel, name):
  await channel.send(name + " need rolled a " + str(random_num()) + "!")

async def greed(channel, name):
  await channel.send(name + " greed rolled a " + str(random_num()) + "!")

async def dkp(channel, author, name):
  await channel.send(name + " you have " + str(get_dkp(author.id)) + " dkp!")

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
      user=client.get_user(result[1])
      message += user.name + " - " + str(result[3]) + " dkp\n"
  await channel.send(message)

async def countdown(channel):
  release = datetime.datetime(2019, 8, 26)
  current = datetime.datetime.now()
  togo = release - current
  await channel.send("There are only " + str(togo.days) + " days until classic is released!")

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
  elif operation == "need":
    await need(channel, name)
  elif operation == "greed":
    await greed(channel, name)
  elif operation == "dkp":
    await dkp(channel, author, name)
  elif operation == "list":
    await listAcc(client,channel)
  elif operation == "countdown":
    await countdown(channel)
    
  

token = open(path+"/token", "r").readline()
print(token)
client = discord.Client()

@client.event
async def on_ready(): #This runs once when connected
  print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
  #Don't respond to self
  if not message.author == client.user:
    await parse_command(client,message.channel,message.author,message.author.name,message.content)
  print(f"{message.channel}: {message.author}: {message.author.name}: {message.content}")

client.run(token.strip())
