import random


def generate_name_local():
    first_names = ['Aldor', 'Brienne', 'Cassius', 'Darian', 'Eleanora', 'Felix', 'Gwen', 'Hugo', 'Isadora', 'Jareth', 'Kael', 'Lysandra', 'Magnus', 'Niamh', 'Ophelia', 'Percival', 'Quentin', 'Rhiannon', 'Soren', 'Thalia', 'Ursula', 'Vesper', 'Wren', 'Xander', 'Yara', 'Zephyr', 'Ludmila', 'Sylvia', 'Alleria']
    last_names = ['Ambershield', 'Bridgerunner', 'Cloudwatcher', 'Doombringer', 'Eaglesight', 'Fireforge', 'Goldweaver', 'Hawkflight', 'Ironheart', 'Jadewalker', 'Kingslayer', 'Lionheart', 'Moonwhisper', 'Nightshade', 'Oakenshield', 'Proudwing', 'Greyrat', 'Ravenstorm', 'Silverhand', 'Thornbloom', 'Umbercoat', 'Violetclaw', 'Whitewind', 'Xenonblade', 'Yellowbrook', 'Proudmore']
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    return f'{first_name} {last_name}'


def dice_roll(dice_count, dice_sides, modifier, best_of, worst_of):
    dice_result = []
    for dice in range(1, dice_count+1):
        dice_result.append(random.randint(1, dice_sides) + modifier)
    if best_of:
        modified_result = sorted(dice_result)
        modified_result = modified_result[dice_count-best_of:]
    elif worst_of:
        modified_result = sorted(dice_result)
        modified_result = modified_result[:best_of]
    else:
        modified_result = dice_result
    return modified_result

