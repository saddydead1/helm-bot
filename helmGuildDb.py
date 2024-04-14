import psycopg2
import helmPlayerDb


def createTable():
    conn = helmPlayerDb.connectDb()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS Government (name TEXT NOT NULL PRIMARY KEY, color TEXT NOT NULL UNIQUE, "
                "discord_channel_id BIGINT NOT NULL, discord_role_id BIGINT NOT NULL, flag TEXT, display_name TEXT "
                "NOT NULL, discord_leader_role_id BIGINT NOT NULL)")
    cur.execute("CREATE TABLE IF NOT EXISTS State (dimension TEXT NOT NULL, center_z INTEGER NOT NULL, center_x "
                "INTEGER NOT NULL, government TEXT NOT NULL REFERENCES Government ON DELETE CASCADE, name TEXT NOT NULL PRIMARY KEY, UNIQUE(dimension, center_z, center_x))")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS Citizens (player BIGINT NOT NULL PRIMARY KEY REFERENCES Player ON DELETE CASCADE, "
        "government TEXT NOT NULL REFERENCES Government ON DELETE CASCADE, role TEXT NOT NULL)")
    conn.commit()
    conn.close()


# создание гильдии  БЕЗ ФЛАГА
def createGuild(name, display_name, color, discord_channel_id, discord_role_id, leader_role):
    conn = helmPlayerDb.connectDb()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO Government (name, color, discord_channel_id, discord_role_id, display_name, "
        "discord_leader_role_id) VALUES (%s, %s, %s, %s, %s, %s)",
        (name, color, discord_channel_id, discord_role_id, display_name, leader_role))
    conn.commit()
    conn.close()


def checkMember(discord_id):
    conn = helmPlayerDb.connectDb()
    cur = conn.cursor()
    cur.execute("SELECT EXISTS(SELECT 1 FROM Player WHERE discord_id=%s)", (discord_id,))
    n = cur.fetchone()
    conn.commit()
    conn.close()
    return n[0]


def checkGuild(name):
    conn = helmPlayerDb.connectDb()
    cur = conn.cursor()
    cur.execute("SELECT EXISTS(SELECT 1 FROM Government WHERE name=%s)", (name,))
    n = cur.fetchone()
    conn.commit()
    conn.close()
    return n[0]


def addMember(discord_id, government, role):
    conn = helmPlayerDb.connectDb()
    cur = conn.cursor()
    cur.execute("INSERT INTO Citizens (player, government, role) VALUES (%s, %s, %s)",
                (discord_id, government, role))
    conn.commit()
    conn.close()


def getDisplayName(name):
    conn = helmPlayerDb.connectDb()
    cur = conn.cursor()
    cur.execute("SELECT display_name FROM Government WHERE name=%s", (name,))
    displayname = cur.fetchone()
    conn.commit()
    conn.close()
    return displayname[0]


def getColor(name):
    conn = helmPlayerDb.connectDb()
    cur = conn.cursor()
    cur.execute("SELECT color FROM Government WHERE name=%s", (name,))
    color = cur.fetchone()
    conn.commit()
    conn.close()
    return color[0]


def getLeaderRoleId(name):
    conn = helmPlayerDb.connectDb()
    cur = conn.cursor()
    cur.execute("SELECT discord_leader_role_id FROM Government WHERE name=%s", (name,))
    idrole = cur.fetchone()
    conn.commit()
    conn.close()
    return idrole[0]

def getGuildRole(name):
    conn = helmPlayerDb.connectDb()
    cur = conn.cursor()
    cur.execute("SELECT discord_role_id FROM Government WHERE name=%s", (name,))
    idrole = cur.fetchone()
    conn.commit()
    conn.close()
    return idrole[0]

def removePlayer(member):
    conn = helmPlayerDb.connectDb()
    cur = conn.cursor()
    cur.execute("DELETE FROM Citizens WHERE player=%s", (member,))
    conn.commit()
    conn.close()

def removeGuild(name):
    conn = helmPlayerDb.connectDb()
    cur = conn.cursor()
    cur.execute('DELETE FROM Government WHERE name=%s', (name,))
    conn.commit()
    conn.close()

def getRole(player):
    conn = helmPlayerDb.connectDb()
    cur = conn.cursor()
    cur.execute("SELECT role FROM Citizens WHERE player=%s", (player,))
    role = cur.fetchone()
    conn.commit()
    conn.close()
    return role[0]

def getForum(name):
    conn = helmPlayerDb.connectDb()
    cur = conn.cursor()
    cur.execute("SELECT discord_channel_id FROM Government WHERE name=%s", (name,))
    id = cur.fetchone()
    conn.commit()
    conn.close()
    return id[0]