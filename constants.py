dnd_skill_map = {
    "Acrobatics": 0, "Animal Handling": 0, "Arcana": 0, "Athletics": 0, "Deception": 0,
    "History": 0, "Insight": 0, "Intimidation": 0, "Investigation": 0, "Medicine": 0,
    "Nature": 0, "Perception": 0, "Performance": 0, "Persuasion": 0, "Religion": 0,
    "Sleight of Hand": 0, "Stealth": 0, "Survival": 0
}

dnd_ability_map = {"STR": 0, "DEX": 0, "CON": 0, "INT": 0, "WIS": 0, "CHA": 0}

allowed_race_list = ["Human", "Elf", "Dwarf", "Halfling", "Dragonborn",
                     "Gnome", "Half-Elf", "Half-Orc", "Tiefling"]

allowed_background_list = ["Acolyte", "Charlatan", "Criminal", "Entertainer", "Folk Hero",
                           "Guild Artisan", "Hermit", "Noble", "Outlander", "Sage", "Sailor",
                           "Soldier", "Urchin"]

dnd_class_proficiency_map = {
    'Barbarian': {
        'pick_options': 2,
        'skill_proficiencies': ['Animal Handling', 'Athletics', 'Intimidation', 'Nature', 'Perception', 'Survival']
    },
    'Bard': {
        'pick_options': 3,
        'skill_proficiencies': 'all'
    },
    'Cleric': {
        'pick_options': 2,
        'skill_proficiencies': ['History', 'Insight', 'Medicine', 'Persuasion', 'Religion']
    },
    'Druid': {
        'pick_options': 2,
        'skill_proficiencies': ['Arcana', 'Animal Handling', 'Insight', 'Medicine', 'Nature', 'Perception', 'Religion', 'Survival']
    },
    'Fighter': {
        'pick_options': 2,
        'skill_proficiencies': ['Acrobatics', 'Animal Handling', 'Athletics', 'History', 'Insight', 'Intimidation', 'Perception', 'Survival']
    },
    'Monk': {
        'pick_options': 2,
        'skill_proficiencies': ['Acrobatics', 'Athletics', 'History', 'Insight', 'Religion', 'Stealth']
    },
    'Paladin': {
        'pick_options': 2,
        'skill_proficiencies': ['Athletics', 'Insight', 'Intimidation', 'Medicine', 'Persuasion', 'Religion']
    },
    'Ranger': {
        'pick_options': 3,
        'skill_proficiencies': ['Animal Handling', 'Athletics', 'Insight', 'Investigation', 'Nature', 'Perception', 'Stealth', 'Survival']
    },
    'Rogue': {
        'pick_options': 4,
        'skill_proficiencies': ['Acrobatics', 'Athletics', 'Deception', 'Insight', 'Intimidation', 'Investigation', 'Perception', 'Performance', 'Persuasion', 'Sleight of Hand', 'Stealth']
    },
    'Sorcerer': {
        'pick_options': 2,
        'skill_proficiencies': ['Arcana', 'Deception', 'Insight', 'Intimidation', 'Persuasion', 'Religion']
    },
    'Warlock': {
        'pick_options': 2,
        'skill_proficiencies': ['Arcana', 'Deception', 'History', 'Intimidation', 'Investigation', 'Nature', 'Religion']
    },
    'Wizard': {
        'pick_options': 2,
        'skill_proficiencies': ['Arcana', 'History', 'Insight', 'Investigation', 'Medicine', 'Religion']
    }
}

skill_ability_map = {
    'Acrobatics': 'DEX',
    'Animal Handling': 'WIS',
    'Arcana': 'INT',
    'Athletics': 'STR',
    'Deception': 'CHA',
    'History': 'INT',
    'Insight': 'WIS',
    'Intimidation': 'CHA',
    'Investigation': 'INT',
    'Medicine': 'WIS',
    'Nature': 'INT',
    'Perception': 'WIS',
    'Performance': 'CHA',
    'Persuasion': 'CHA',
    'Religion': 'INT',
    'Sleight of Hand': 'DEX',
    'Stealth': 'DEX',
    'Survival': 'WIS'
}

#put it in enum
BASE_GEN = 0
RACE = 1
BG = 2
SKILLS = 3
FREEZE = 4

tag_marn = '<@371229251501948929>'