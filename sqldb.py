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


# Initializes tables and some data in the database if they don't exist
def init_db():
  sql_commands = []
  sql_commands.append("PRAGMA foreign_keys = ON;")
  sql_commands.append(""" CREATE TABLE IF NOT EXISTS professions (
                            id integer NOT NULL PRIMARY KEY,
                            name text NOT NULL
                          ); """)
  sql_commands.append(""" INSERT OR IGNORE INTO professions (id, name) VALUES
                            (0, "None"),
                            (1, "Alchemy"),
                            (2, "Blacksmithing"),
                            (3, "Enchanting"),
                            (4, "Engineering"),
                            (5, "Herbalism"),
                            (6, "Leatherworking"),
                            (7, "Mining"),
                            (8, "Skinning"),
                            (9, "Tailoring"); """)
  sql_commands.append(""" CREATE TABLE IF NOT EXISTS players (
                            discord_id integer NOT NULL PRIMARY KEY,
                            dkp integer NOT NULL DEFAULT 0 CHECK(dkp >= 0),
                            need_rolls integer NOT NULL DEFAULT 0 CHECK(need_rolls >= 0),
                            greed_rolls integer NOT NULL DEFAULT 0 CHECK(greed_rolls >= 0),
                            character_name text UNIQUE DEFAULT NULL,
                            joined_at datetime DEFAULT CURRENT_TIMESTAMP,
                            prof1 int NOT NULL DEFAULT 0,
                            prof2 int NOT NULL DEFAULT 0,
                            status text DEFAULT "active" CHECK(status in ("active", "inactive", "abandoned", "kicked")),
                            CONSTRAINT fk_prof1 FOREIGN KEY(prof1) REFERENCES professions(id) ON DELETE SET DEFAULT,
                            CONSTRAINT fk_prof2 FOREIGN KEY(prof2) REFERENCES professions(id) ON DELETE SET DEFAULT
                          ) WITHOUT ROWID; """)

  try:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for sql_command in sql_commands:
      c.execute(sql_command)
    conn.commit()
  except Error as e:
    print(e)
  finally:
    conn.close()


# given a db connection, creates player in db if they don't already exist
def create_player(conn, discord_id):
  sql = """ INSERT OR IGNORE INTO players(discord_id)
              VALUES(?) """
  to_insert = (discord_id,)
  try:
    cur = conn.cursor()
    cur.execute(sql, to_insert)
    conn.commit()
    #else do nothing
  except Error as e:
    print(e)


# creates player in db if they don't already exist
def add_player(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    create_player(conn, discord_id)
  except Error as e:
    print(e)
  finally:
    conn.close()


def set_status_abandoned(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE players SET status = \"abandoned\" WHERE discord_id=" + str(discord_id))
    conn.commit()
  except Error as e:
    print(e)
  finally:
    conn.close()


def get_player(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    create_player(conn, discord_id)
    cur = conn.cursor()
    cur.execute("SELECT * FROM players WHERE discord_id=" + str(discord_id) )
    result = cur.fetchone()
    return result
  except Error as e:
    print(e)
  finally:
    conn.close()


def get_player_by_char_name(char_name):
  try:
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM players WHERE LOWER(character_name)=LOWER(?)",(char_name,))
    result = cur.fetchone()
    return result
  except Error as e:
    print(e)
  finally:
    conn.close()


def get_all_players():
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
    create_player(conn, discord_id)
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
    create_player(conn, discord_id)
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
    create_player(conn, discord_id)
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
    create_player(conn, discord_id)
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
    create_player(conn, discord_id)
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
    create_player(conn, discord_id)
    cur = conn.cursor()
    #the parens sanitize input i guess
    cur.execute("UPDATE OR IGNORE players SET character_name=? WHERE discord_id=" + str(discord_id), (name,))
    conn.commit()
  except Error as e:
    print(e)
  finally:
    conn.close()


def get_prof_id(prof_name):
  try:
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id FROM professions WHERE LOWER(name)=LOWER(?)", (prof_name,))
    result = cur.fetchone()
    return result[0] if result else None
  except Error as e:
    print(e)
  finally:
    conn.close()


def set_prof1(discord_id, prof_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    create_player(conn, discord_id)
    cur = conn.cursor()
    #the parens sanitize input i guess
    cur.execute("UPDATE players SET prof1=? WHERE discord_id=" + str(discord_id), (prof_id,))
    conn.commit()
  except Error as e:
    print(e)
  finally:
    conn.close()


def set_prof2(discord_id, prof_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    create_player(conn, discord_id)
    cur = conn.cursor()
    #the parens sanitize input i guess
    cur.execute("UPDATE players SET prof2=? WHERE discord_id=" + str(discord_id), (prof_id,))
    conn.commit()
  except Error as e:
    print(e)
  finally:
    conn.close()


def get_prof1(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    create_player(conn, discord_id)
    cur = conn.cursor()
    #the parens sanitize input i guess
    cur.execute("SELECT name FROM professions INNER JOIN players ON players.prof1 = professions.id WHERE players.discord_id=" + str(discord_id))
    conn.commit()
    return cur.fetchone()[0]
  except Error as e:
    print(e)
  finally:
    conn.close()


def get_prof2(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    create_player(conn, discord_id)
    cur = conn.cursor()
    #the parens sanitize input i guess
    cur.execute("SELECT name FROM professions INNER JOIN players ON players.prof2 = professions.id WHERE players.discord_id=" + str(discord_id))
    conn.commit()
    return cur.fetchone()[0]
  except Error as e:
    print(e)
  finally:
    conn.close()


def get_joined_at(discord_id):
  try:
    conn = sqlite3.connect(DB_FILE)
    create_player(conn, discord_id)
    cur = conn.cursor()
    cur.execute("SELECT joined_at FROM players WHERE discord_id=" + str(discord_id))
    return cur.fetchone()[0]
  except Error as e:
    print(e)
  finally:
    conn.close()
