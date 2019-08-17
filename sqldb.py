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


def create_table(conn):
  sql_create_players_table = """ CREATE TABLE IF NOT EXISTS players (
                                    id integer PRIMARY KEY,
                                    discord_id integer NOT NULL,
                                    dkp integer,
                                    need_rolls integer,
                                    greed_rolls integer,
                                    account_name text,
                                    join_date datetime,
                                    prof1 integer,
                                    prof2 integer
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
  sql = '''INSERT INTO players(discord_id,dkp,need_rolls,greed_rolls,account_name,join_date,prof1,prof2)
           VALUES(?,?,?,?,?,?,?,?)  '''
  to_insert = (discord_id,0,0,0,"",str(datetime.datetime.now()),0,0)
  try:
    cur = conn.cursor()
    cur.execute(sql, to_insert)
    conn.commit()
    #else do nothing
  except Error as e:
    print(e)

def check_player_table(conn):
  conn = sqlite3.connect(DB_FILE)
  create_table(conn)
  return True

def add_account_record(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    create_account_if_doesnt_exist(conn, discord_id)
  except Error as e:
    print(e)
  finally:
    conn.close()

def remove_account_record(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
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
    create_account_if_doesnt_exist(conn, discord_id)
    cur = conn.cursor()
    #the parens sanitize input i guess
    cur.execute("UPDATE players SET account_name=? WHERE discord_id=" + str(discord_id), (name,))
    conn.commit()
  except Error as e:
    print(e)
  finally:
    conn.close()

def set_prof1(discord_id, profID):
  try:
    conn = sqlite3.connect(DB_FILE)
    create_account_if_doesnt_exist(conn, discord_id)
    cur = conn.cursor()
    #the parens sanitize input i guess
    cur.execute("UPDATE players SET prof1=? WHERE discord_id=" + str(discord_id), (profID,))
    conn.commit()
  except Error as e:
    print(e)
  finally:
    conn.close()

def set_prof2(discord_id, profID):
  try:
    conn = sqlite3.connect(DB_FILE)
    create_account_if_doesnt_exist(conn, discord_id)
    cur = conn.cursor()
    #the parens sanitize input i guess
    cur.execute("UPDATE players SET prof2=? WHERE discord_id=" + str(discord_id), (profID,))
    conn.commit()
  except Error as e:
    print(e)
  finally:
    conn.close()

def get_prof1(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    create_account_if_doesnt_exist(conn, discord_id)
    cur = conn.cursor()
    #the parens sanitize input i guess
    cur.execute("SELECT prof1 FROM players WHERE discord_id=" + str(discord_id))
    conn.commit()
    return cur.fetchone()[0]
  except Error as e:
    print(e)
  finally:
    conn.close()

def get_prof2(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    create_account_if_doesnt_exist(conn, discord_id)
    cur = conn.cursor()
    #the parens sanitize input i guess
    cur.execute("SELECT prof2 FROM players WHERE discord_id=" + str(discord_id))
    conn.commit()
    return cur.fetchone()[0]
  except Error as e:
    print(e)
  finally:
    conn.close()

def get_join_date(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    create_account_if_doesnt_exist(conn, discord_id)
    cur = conn.cursor()
    cur.execute("SELECT join_date FROM players WHERE discord_id=" + str(discord_id))
    return cur.fetchone()[0]
  except Error as e:
    print(e)
  finally:
    conn.close()
