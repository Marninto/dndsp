import json
import datetime

import mysql.connector

# Connect to the database
db_config = {
  'user': 'marninto',
  'password': '',
  'host': 'localhost',
  'database': 'dnd',
  'raise_on_warnings': True
}


def enroll(discord_id):
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        cursor.execute(f"SELECT * FROM discord_summary where discord_id={discord_id}")
        rows = cursor.fetchall()
        if rows:
            return True, 'exists'
        else:
            add_character = ("INSERT INTO discord_summary "
                             "(discord_id, daily_tokens, gold, daily_refresh, created) "
                             "VALUES (%s, %s, %s, %s, %s)")
            data_character = (discord_id, 0, 0, datetime.datetime.now(), datetime.datetime.now())
            cursor.execute(add_character, data_character)
            cnx.commit()

            cursor.close()
            cnx.close()
            return True, 'created'
    except Exception as e:
        print(e)
        return False, e


def test():
    # Open a cursor to perform database operations
    cnx = mysql.connector.connect(**db_config)
    cur = cnx.cursor()

    # Execute a SELECT statement to retrieve some data
    cur.execute("SELECT * FROM discord_summary")

    # Fetch the results and print them out
    rows = cur.fetchall()
    print(rows)
    for row in rows:
        print(row)

    # Close the cursor and connection
    cur.close()
    cnx.close()


def check_onboard_status(discord_id):
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    cursor.execute(f"SELECT id FROM discord_summary where discord_id={discord_id}")
    result = cursor.fetchone()
    data = None
    if result:
        data = result[0]
    cursor.close()
    cnx.close()
    return data


def update_char_gen_progress(char_id, progress_state, progress_value, creation_stage):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    update_query = f"UPDATE characters SET {progress_state} = %s, creation_stage = %s WHERE char_id = %s"
    cursor.execute(update_query, (progress_value, creation_stage, char_id))
    cursor.close()
    conn.close()


def check_player_chars(discord_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(f"SELECT id FROM discord_summary WHERE discord_id = {discord_id}")
    player_id = cursor.fetchone()
    if player_id is None:
        data = json.dumps({'success': False, 'player_id': 0})
        cursor.close()
        conn.close()
        return data
    else:
        query = "SELECT id FROM player_characters WHERE player_id = %s"
        cursor.execute(query, (player_id[0],))
        char_id_qs = cursor.fetchall()
        if len(char_id_qs) >= 1:
            data = json.dumps({'success': True, 'player_id': char_id_qs[-1][0] if char_id_qs else None})
        else:
            data = json.dumps({'success': False, 'count': 0})
        cursor.close()
        conn.close()
        return data


def get_char_ability_details(char_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(f"""SELECT pc.char_name, pc.ability_map, pc.char_freeze, pc.picked_proficiencies, pb.bg_name, pb.proficiency_list, 
                    pc.ability_score_improve, cl.hit_dice, cl.class_name, cl.saving_throw_proficiency, pc.max_hp, pr.race_name 
                    FROM player_characters AS pc
                    left JOIN player_backgrounds AS pb ON pc.background_id = pb.id 
                    left JOIN player_classes AS cl ON pc.class_id = cl.id 
                    left JOIN player_races AS pr on pr.id = pc.race_id
                    WHERE pc.id = {char_id}""")
    result = cursor.fetchone()
    data = None if result is None else json.dumps({
            'char_name': result[0],
            'ability_map': result[1],
            'char_freeze': result[2],
            'picked_proficiencies': result[3],
            'bg_name': result[4],
            'proficiency_list': result[5],
            'ability_score_improve': result[6],
            'hit_dice': result[7],
            'class_name': result[8],
            'saving_throw_proficiency': result[9],
            'max_hp': result[10],
            'race_name': result[11]
        })
    cursor.close()
    conn.close()
    return data


def fetch_race_map():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(f"""SELECT race_name, ability_modifier FROM player_races""")
    result = cursor.fetchall()
    data = {}
    for race_data in result:
        data[race_data[0]] = race_data[1]
    cursor.close()
    conn.close()
    return data


def generate_custom_char(ability_map, char_name, max_hp, player_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Prepare the INSERT statement
    query = """
        INSERT INTO player_characters (char_name, class_id, player_id, ability_map, 
        char_freeze, max_hp) 
        VALUES (%s, %s, %s, %s, %s, %s)
        """
    # Convert the maps to JSON strings
    ability_map_json = json.dumps(ability_map)

    # Set char_freeze to False as the character is newly created
    char_freeze = False

    # Execute the query
    cursor.execute(query, (char_name, 12, player_id, ability_map_json,
                           char_freeze, max_hp))
    inserted_id = cursor.lastrowid

    # Commit the transaction
    conn.commit()

    # Close the cursor and connection
    cursor.close()
    conn.close()
    return inserted_id


def generate_quickbuild_character(ability_map, ability_score, picked_proficiency, player_id, race_id, class_id, background_id, name, max_hp):
    # Connect to the database
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Prepare the INSERT statement
    query = """
    INSERT INTO player_characters (char_name, class_id, player_id, ability_map, background_id, 
    char_freeze, picked_proficiencies, race_id, ability_score_improve, max_hp) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    # Convert the maps to JSON strings
    ability_map_json = json.dumps(ability_map)
    ability_score_json = json.dumps(ability_score)

    # Set char_freeze to False as the character is newly created
    char_freeze = True

    # Execute the query
    cursor.execute(query, (name, class_id, player_id, ability_map_json, background_id,
    char_freeze, picked_proficiency, race_id, ability_score_json, max_hp))

    # Commit the transaction
    conn.commit()

    # Close the cursor and connection
    cursor.close()
    conn.close()


def get_class_id_from_name(class_name):
    # Connect to the database
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Prepare the SELECT statement
    query = """
    SELECT id FROM player_classes WHERE class_name = %s
    """
    cursor.execute(query, (class_name,))

    # Fetch the result
    result = cursor.fetchone()
    if result is None:
        print(f"Class not found: {class_name}")

    class_id = result[0] if result is not None else None

    # Close the cursor and connection
    cursor.close()
    conn.close()

    return class_id


def get_score_modifier(race_id):
    # Connect to the database
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Prepare the SELECT statement
    query = """
    SELECT ability_modifier FROM player_races WHERE id = %s
    """
    cursor.execute(query, (race_id,))

    # Fetch the result
    result = cursor.fetchone()
    if result is None:
        print(f"Race not found: {race_id}")

    ability_modifier = json.loads(result[0]) if result is not None else None  # convert JSON string to dict

    # Close the cursor and connection
    cursor.close()
    conn.close()

    return ability_modifier
