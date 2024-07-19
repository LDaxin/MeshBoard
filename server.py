import meshtastic
import meshtastic.serial_interface
import sqlite3
import time
import json
from datetime import datetime as dt
from pubsub import pub

# Variables -----------------------------------------------------------------------------
serverMeshId = "!e0d032c0"

# initialize database -------------------------------------------------------------------
conn  = sqlite3.connect('data.db', check_same_thread=False)

c = conn.cursor()
c.execute('''create table if not exists user (
            id integer primary key autoincrement,
            meshId text not null,
            longName text not null,
            shortName text not null,
            macAddr text not null,
            menuNum integer default 0,
            language integer default 0
            )
          ''')
conn.commit()

c.execute('''create table if not exists messageBord (
            id integer primary key autoincrement,
            message text not null,
            dateTime text not null,
            userId not null
            )
          ''')
conn.commit()

# interact with Database -----------------------------------------------------------------

def fetchUserData(meshId, interface):
    if interface.nodes:
        for n in interface.nodes.values():
            if n["user"]["id"] == meshId:
                return n

def storeUserData(data):
    c.execute("INSERT INTO user (meshId, longName, shortName, macAddr) VALUES (:id, :long, :short, :mac)", 
              {'id': data['user']['id'], 'long': data["user"]["longName"], 'short': data['user']['shortName'], 'mac': data['user']['macaddr']}
              )
    conn.commit()

# menus -----------------------------------------------------------------------------------
menuStruct = [[1, 2], [3, 4, 0]]
langPack = []

# load the Menu Languages
with open("language.json") as f:
    lang = json.load(f)
    langPack = lang["list"]

def direction(data ,interface):
    pass


def onReceive(packet, interface): # called when a packet arrives
    with open('log.txt', 'a') as f:
        f.writelines(f'{packet}\n\n--------------------------------------------------------------------------\n')
    if packet["toId"] == serverMeshId:
        print(packet["decoded"]["text"])

        userData = c.execute("select * from user where meshId = :id", {'id':packet['fromId']}).fetchall()

        if len(userData) == 0:
            
            storeUserData(fetchUserData(packet['fromId'], interface))
            userData = c.execute("select * from user where meshId = :id", {'id':packet['fromId']}).fetchall()
            interface.sendText(langPack[userData[0][6]]["newUserAdd"], userData[0][1])
        elif len(userData) == 1:
            direction(packet, interface)
        else:
            print("there are to many users")


def onConnection(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
    # defaults to broadcast, specify a destination ID if you wish
    # interface.sendText("hello mesh")
    print("connected")

pub.subscribe(onReceive, "meshtastic.receive")
pub.subscribe(onConnection, "meshtastic.connection.established")

try:
    interface = meshtastic.serial_interface.SerialInterface(devPath="/dev/ttyACM0")
    while True:
        time.sleep(1000)
except Exception as ex:
    print(ex)

conn.close()
