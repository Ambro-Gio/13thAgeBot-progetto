import re
from telegram.ext import Updater, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters, ConversationHandler
import utility_functions as uf
import json

# character creation stages
RACE, RACE_ATTRIBUTES, CLASS, CLASS_ATTRIBUTES, BACKGROUND,\
    BACKGROUND_POINTS, CLASS_TALENT, TALENT_2, CLASS_MPS, CLASS_FEATS, STATS, ONE_UNIQUE_THING,\
    ARMOR, MELEE, RANGED, SHIELD, ICON, ICON_RELATIONSHIP, ICON_RELATIONSHIP_POINTS = range(19)

# user data temp info
tmp_user_data = {}


def main():
    updater = Updater(token='5194748209:AAGiz8OdzZpnzb-JpMX-s34d0Xl-dQnHgW8', use_context=True)
    dispatcher = updater.dispatcher

    # handler for the /start command
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    # handler for /roll
    roll_handler = CommandHandler('roll', roll)
    dispatcher.add_handler(roll_handler)

    # handler for /save_currency
    save_currency_handler = CommandHandler('save_currency', save_currency)
    dispatcher.add_handler(save_currency_handler)

    # handler for /pay_currency
    pay_currency_handler = CommandHandler('pay_currency', pay_currency)
    dispatcher.add_handler(pay_currency_handler)

    # handler for /give_item
    give_item_handler = CommandHandler('give_item', add_item)
    dispatcher.add_handler(give_item_handler)

    # handler for /leave_item
    leave_item_handler = CommandHandler('leave_item', leave_item)
    dispatcher.add_handler(leave_item_handler)

    # handler for /give_magic_item
    give_magic_item_handler = CommandHandler('give_magic_item', add_magic_item)
    dispatcher.add_handler(give_magic_item_handler)

    # handler for /leave_magic_item
    leave_magic_item_handler = CommandHandler('leave_magic_item', leave_magic_item)
    dispatcher.add_handler(leave_magic_item_handler)

    # handler for /get_sheet
    get_sheet_handler = CommandHandler('get_sheet', get_player_sheet)
    dispatcher.add_handler(get_sheet_handler)

    # handler for /help
    help_handler = CommandHandler('help', help_f)
    dispatcher.add_handler(help_handler)

    pc_creation_handler = ConversationHandler(
        entry_points=[(CommandHandler('new_pc', new_pc_start))],
        states={
            RACE: [MessageHandler(Filters.text & ~Filters.command, new_pc_race)],
            RACE_ATTRIBUTES: [MessageHandler(Filters.text & ~Filters.command, new_pc_race_attributes)],
            CLASS: [MessageHandler(Filters.text & ~Filters.command, new_pc_class)],
            CLASS_ATTRIBUTES: [MessageHandler(Filters.text & ~Filters.command, new_pc_class_attributes)],
            CLASS_TALENT: [MessageHandler(Filters.text & ~Filters.command, new_pc_class_talent)],
            TALENT_2: [MessageHandler(Filters.text & ~Filters.command, new_pc_talent2)],
            CLASS_MPS: [MessageHandler(Filters.text & ~Filters.command, new_pc_mps)],
            CLASS_FEATS: [MessageHandler(Filters.text & ~Filters.command, new_pc_feat)],
            STATS: [MessageHandler(Filters.text & ~Filters.command, new_pc_stats)],
            ONE_UNIQUE_THING: [MessageHandler(Filters.text & ~Filters.command, new_pc_one_unique_thing)],
            BACKGROUND: [MessageHandler(Filters.text & ~Filters.command, new_pc_background)],
            BACKGROUND_POINTS: [MessageHandler(Filters.text & ~Filters.command, new_pc_background_points)],
            ARMOR: [MessageHandler(Filters.text & ~Filters.command, new_pc_armor_choice)],
            MELEE: [MessageHandler(Filters.text & ~Filters.command, new_pc_melee_choice)],
            RANGED: [MessageHandler(Filters.text & ~Filters.command, new_pc_ranged_choice)],
            ICON: [MessageHandler(Filters.text & ~Filters.command, new_pc_icon_choice)],
            ICON_RELATIONSHIP: [MessageHandler(Filters.text & ~Filters.command, new_pc_icon_relationship)],
            ICON_RELATIONSHIP_POINTS: [MessageHandler(Filters.text & ~Filters.command, new_pc_icon_points)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(pc_creation_handler)

    # handler for dice roll inline keyboard
    dice_keyboard_handler = CallbackQueryHandler(gui_dice_roll)
    dispatcher.add_handler(dice_keyboard_handler)

    # handler for unknown commands
    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)

    updater.start_polling()
    updater.idle()

def cancel(update: Update, context: CallbackContext):
    """Cancels character creation"""
    user_id = update.effective_user.name
    # deleting tmp info
    global tmp_user_data
    try:
        del(tmp_user_data[f"{user_id}"])
    except KeyError:
        pass
    update.message.reply_text(
        'Character creation cancelled', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def start(update: Update, context: CallbackContext):
    """start commands. Greets the new user and starts a chat with the bot"""
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="I'm 13thAge_bot!")


def new_pc_start(update: Update, context: CallbackContext):
    """
    Entry point fot the pc creation command. The user is guided through a list of steps to create a new character:
    -name
    -race and class
    -roll for stats
    -one unique thing, backgrounds, feats...
    """
    update.message.reply_text("New Character! Please tell me what their name is!")
    return RACE


def new_pc_race(update: Update, context: CallbackContext):
    """saves player name info, initializes tmp data structure, builds keyboard for race selection"""
    user_id = update.effective_user.name
    pc_name = update.message.text

    # check for user file and if character name is already taken
    try:
        with open(f"json_files/users/{user_id}.json", "r") as fp:
            user_data = json.load(fp)
        pc_name_key = "_".join(pc_name.lower().split())
        if pc_name_key in user_data.keys():
            update.message.reply_text("I'm sorry, you already have a character with this name. Try again...")
            return ConversationHandler.END
    except IOError:
        pass

    # creating new pc and saving them into tmp structure
    with open("json_files/character_sheet.json", "r") as fp:
        new_character = json.load(fp)
    new_character['name'] = pc_name
    # building tmp data structure
    global tmp_user_data
    tmp_user_data[f"{user_id}"] = {}
    tmp_user_data[f"{user_id}"]["tmp_character"] = new_character
    tmp_user_data[f"{user_id}"]["background_points"] = 0
    tmp_user_data[f"{user_id}"]["icon_relationship_points"] = 0
    tmp_user_data[f"{user_id}"]["talent_points"] = 0
    tmp_user_data[f"{user_id}"]["feat_points"] = 0
    tmp_user_data[f"{user_id}"]["feat_list"] = []
    tmp_user_data[f"{user_id}"]["mps_points"] = 0

    with open("json_files/races.json", "r") as fp:
        races = json.load(fp)
    # acquiring list of available races
    races = [*races]

    reply_keyboard = []
    for race in races:
        reply_keyboard.append([race])

    update.message.reply_text(
        'Neat! What race would you like your character to be?',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Choose your race'
        ),
    )

    return RACE_ATTRIBUTES


def new_pc_race_attributes(update: Update, context: CallbackContext):
    """
    saves race selection, and builds virtual keyboard for race attributes selection
    """
    user_id = user_id = update.effective_user.name
    pc_race = update.message.text

    # recovering race specific info
    with open("json_files/races.json") as fp:
        race_info = json.load(fp)[f"{pc_race}"]

    # saving race choices
    global tmp_user_data
    tmp_user_data[f"{user_id}"]["tmp_character"]["race"] = pc_race
    tmp_user_data[f"{user_id}"]["tmp_character"]["racial_power"] = race_info["racial_power"]
    for racial_feat in race_info["racial_feats"]:
        tmp_user_data[f"{user_id}"]["feat_list"].append(racial_feat)
    if pc_race == "human":
        tmp_user_data[f"{user_id}"]["feat_points"] += 1

    # building keyboard for attribute bonus choice
    reply_keyboard = []
    for attribute in race_info["bonus"]["modifier"]:
        reply_keyboard.append([attribute])

    update.message.reply_text(
        'Please choose your attribute bonus\n',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='attribute bonus'
        ),
    )

    return CLASS


def new_pc_class(update: Update, context: CallbackContext):
    """saves race attributes selection, and builds virtual keyboard for class selection"""
    user_id = update.effective_user.name
    pc_stat_attribute = update.message.text

    global tmp_user_data
    tmp_user_data[f"{user_id}"]["tmp_character"]["stats"][f"{pc_stat_attribute}"]["value"] += 2

    # building keyboard for race selection
    with open("json_files/classes.json", "r") as fp:
        class_info = json.load(fp)
        classes = [*class_info]
    reply_keyboard = []
    for class_elem in classes:
        reply_keyboard.append([class_elem])
    update.message.reply_text(
        'Please choose your class\n',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='class'
        ),
    )
    return CLASS_ATTRIBUTES


def new_pc_class_attributes(update: Update, context: CallbackContext):
    """saves class info and builds keyboard for class attributes selection"""
    user_id = update.effective_user.name
    pc_class = update.message.text

    # retrieving class info:
    with open("json_files/classes.json", "r") as fp:
        class_info = json.load(fp)[f"{pc_class}"]

    # saving class
    global tmp_user_data
    tmp_user_data[f"{user_id}"]["tmp_character"]["class"] = pc_class
    tmp_user_data[f"{user_id}"]["tmp_character"]["balance"] = class_info["balance"]
    tmp_user_data[f"{user_id}"]["tmp_character"]["melee"] = class_info["melee"]
    tmp_user_data[f"{user_id}"]["tmp_character"]["ranged"] = class_info["ranged"]
    tmp_user_data[f"{user_id}"]["tmp_character"]["recoveries"]["max"] = class_info["stats"]["recoveries"]
    tmp_user_data[f"{user_id}"]["tmp_character"]["recoveries"]["current"] = class_info["stats"]["recoveries"]
    tmp_user_data[f"{user_id}"]["tmp_character"]["hit_points"] = class_info["stats"]["base_hp"]
    tmp_user_data[f"{user_id}"]["tmp_character"]["physical_defense"] = class_info["stats"]["base_pd"]
    tmp_user_data[f"{user_id}"]["tmp_character"]["mental_defense"] = class_info["stats"]["base_md"]
    tmp_user_data[f"{user_id}"]["tmp_character"]["recovery_roll"] = class_info["stats"]["recovery_dice"]

    tmp_user_data[f"{user_id}"]["background_points"] += class_info["background_points"]
    tmp_user_data[f"{user_id}"]["icon_relationship_points"] += class_info["icon_relationship_points"]
    tmp_user_data[f"{user_id}"]["talent_points"] += class_info["talents_number"]
    tmp_user_data[f"{user_id}"]["feat_points"] += class_info["feats_number"]
    tmp_user_data[f"{user_id}"]["mps_points"] += class_info["mps_number"]

    # building keyboard for class attributes bonus
    reply_keyboard = []
    for attribute in class_info["bonus"]["modifier"]:
        reply_keyboard.append([attribute])

    update.message.reply_text(
        'Please choose your class attribute bonus (must be different from the race bonus)\n',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='attribute bonus'
        ),
    )

    return CLASS_TALENT


def new_pc_class_talent(update: Update, context: CallbackContext):
    """saves class attribute bonus info, builds keyboard for talent selection"""
    user_id = update.effective_user.name
    pc_class_attribute = update.message.text

    # class attribute must be different from race attribute
    global tmp_user_data
    tmp_user_data_local = tmp_user_data[f"{user_id}"]
    # retrieving class info:
    with open("json_files/classes.json", "r") as fp:
        pc_class = tmp_user_data_local["tmp_character"]["class"]
        class_info = json.load(fp)[f"{pc_class}"]

    # check to see if attribute is already been chosen
    if tmp_user_data_local["tmp_character"]["stats"][f"{pc_class_attribute}"]["value"] > 0:
        # building keyboard for class attributes bonus
        reply_keyboard = []
        for attribute in class_info["bonus"]["modifier"]:
            reply_keyboard.append([attribute])
        update.message.reply_text(
            "I'm sorry, you already have chosen this attribute. Try again...",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder='attribute bonus'
            ),
        )

        return CLASS_TALENT

    tmp_user_data_local["tmp_character"]["stats"][f"{pc_class_attribute}"]["value"] += 2

    # building keyboard for talent selection and saving talent list into tmp data structure
    tmp_user_data_local["talent_list"] = []
    reply_keyboard = []
    for talent in class_info["talent"]:
        tmp_user_data_local["talent_list"].append(talent)
        reply_keyboard.append([talent])

    update.message.reply_text(
        'Please choose a talent\n',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='talent'
        ),
    )
    tmp_user_data[f"{user_id}"] = tmp_user_data_local

    return TALENT_2


def new_pc_talent2(update: Update, context: CallbackContext):
    """talent choice is repeated until there are no more talent points"""
    user_id = update.effective_user.name
    pc_talent = update.message.text

    global tmp_user_data
    tmp_user_data_local = tmp_user_data[f"{user_id}"]

    # saving chosen talent
    tmp_user_data_local["tmp_character"]["talents"].append(pc_talent)
    tmp_user_data_local["talent_points"] -= 1
    tmp_user_data_local["talent_list"].remove(f"{pc_talent}")

    tmp_user_data[f"{user_id}"] = tmp_user_data_local

    if tmp_user_data_local["talent_points"] > 0:
        reply_keyboard = []
        for talent in tmp_user_data_local["talent_list"]:
            reply_keyboard.append([talent])
        update.message.reply_text(
            f'Please choose a talent\nPoints remaining: {tmp_user_data_local["talent_points"]}',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder='talent'
            ),
        )
        return TALENT_2

    # building mps list and keyboard
    with open("json_files/classes.json", "r") as fp:
        pc_class_info = json.load(fp)[f"{tmp_user_data_local['tmp_character']['class']}"]
    reply_keyboard = []
    tmp_user_data_local["mps_list"] = []
    for mps in pc_class_info["mps"]:
        reply_keyboard.append([mps]),
        tmp_user_data_local["mps_list"].append(mps)
    tmp_user_data[f"{user_id}"] = tmp_user_data_local

    update.message.reply_text(
        'Please choose one move/power/spell\n',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='mps'
        ),
    )

    return CLASS_MPS


def new_pc_mps(update: Update, context: CallbackContext):
    """saves the chosen mps. The choice is presented again until there are no more points"""
    user_id = update.effective_user.name
    pc_mps = update.message.text

    global tmp_user_data
    tmp_user_data_local = tmp_user_data[f"{user_id}"]

    # saving chosen mps
    tmp_user_data_local["tmp_character"]["mps"].append(pc_mps)
    tmp_user_data_local["mps_points"] -= 1
    tmp_user_data_local["mps_list"].remove(f"{pc_mps}")

    tmp_user_data[f"{user_id}"] = tmp_user_data_local
    if tmp_user_data_local["mps_points"] > 0:
        reply_keyboard = []
        for mps in tmp_user_data_local["mps_list"]:
            reply_keyboard.append([mps])
        update.message.reply_text(
            f'Please choose one move/power/spell\nPoints remaining: {tmp_user_data_local["mps_points"]}',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder='mps'
            ),
        )
        return CLASS_MPS

    # building feats list and keyboard
    with open("json_files/classes.json", "r") as fp:
        pc_class_info = json.load(fp)[f"{tmp_user_data_local['tmp_character']['class']}"]

    # feat is added to the list if it's a class feat, or if it's a feat associated with a talent/mps chosen by user
    for feat in pc_class_info['feat']:
        if feat not in pc_class_info['talent'] and feat not in pc_class_info['mps']:
            tmp_user_data_local['feat_list'].append(feat)
        elif feat in pc_class_info['talent'] and feat in tmp_user_data_local['tmp_character']['talents']:
            tmp_user_data_local['feat_list'].append(feat)
        elif feat in pc_class_info['mps'] and feat in tmp_user_data_local['tmp_character']['mps']:
            tmp_user_data_local['feat_list'].append(feat)

    reply_keyboard = []
    for feat in tmp_user_data_local['feat_list']:
        reply_keyboard.append([feat])

    update.message.reply_text(
        'Please choose one feat\n',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='feat'
        ),
    )

    tmp_user_data[f"{user_id}"] = tmp_user_data_local
    return CLASS_FEATS


def new_pc_feat(update: Update, context: CallbackContext):
    """saves chosen feat. The choice is presented again until there are no more points.
    When feat points is 0, builds keyboard for attribute rolls choice"""
    user_id = update.effective_user.name
    pc_feat = update.message.text

    global tmp_user_data
    tmp_user_data_local = tmp_user_data[f"{user_id}"]

    # saving feat
    tmp_user_data_local["tmp_character"]["feats"].append(pc_feat)
    tmp_user_data_local["feat_points"] -= 1
    tmp_user_data_local["feat_list"].remove(f"{pc_feat}")

    tmp_user_data[f"{user_id}"] = tmp_user_data_local
    if tmp_user_data_local["feat_points"] > 0:
        reply_keyboard = []
        for feat in tmp_user_data_local["feat_list"]:
            reply_keyboard.append([feat])
        update.message.reply_text(
            f'Please choose one feat\nPoints remaining: {tmp_user_data_local["feat_points"]}',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder='feat'
            ),
        )
        return CLASS_FEATS

    # attributes rolls
    tmp_user_data_local["roll_list"] = []
    for i in range(6):
        outcome = uf.dice_roll(4, 6)
        # dropping the lowest result
        outcome['rolls_total'] -= min(outcome['rolls_log'])
        tmp_user_data_local["roll_list"].append(outcome['rolls_total'])

    tmp_user_data_local["roll_list"].sort(reverse=True)
    tmp_user_data[f"{user_id}"] = tmp_user_data_local

    update.message.reply_text(
        f'your dice rolls: {tmp_user_data_local["roll_list"]}'
    )
    # building stat keyboard
    reply_keyboard = []
    for stat in tmp_user_data_local["tmp_character"]["stats"].keys():
          reply_keyboard.append([stat])

    update.message.reply_text(
        f'Please choose one stat to assign the value {tmp_user_data_local["roll_list"][0]}\n',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='choose stat'
        ),
    )
    return STATS


def new_pc_stats(update: Update, context: CallbackContext):
    """saves attribute rolls choice, until every attribute is assigned"""
    user_id = update.effective_user.name
    pc_stat = update.message.text

    global tmp_user_data
    tmp_user_data_local = tmp_user_data[f"{user_id}"]

    #saving stat
    tmp_user_data_local["tmp_character"]["stats"][f"{pc_stat}"]["value"] += tmp_user_data_local["roll_list"].pop(0)
    tmp_user_data[f"{user_id}"] = tmp_user_data_local

    if len(tmp_user_data_local["roll_list"]) > 0:
        # building stat keyboard
        reply_keyboard = []
        for stat in [x for x in tmp_user_data_local["tmp_character"]["stats"].keys() if
                     tmp_user_data_local["tmp_character"]["stats"][f"{x}"]["value"] <= 2]:
            reply_keyboard.append([stat])

        update.message.reply_text(
            f'Please choose one stat to assign the value {tmp_user_data_local["roll_list"][0]}\n',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder='choose stat'
            ),
        )
        return STATS

    # computing modifier values
    for stat in tmp_user_data_local["tmp_character"]["stats"].keys():
        tmp_user_data_local["tmp_character"]["stats"][f"{stat}"]["modifier"] =\
            int((tmp_user_data_local["tmp_character"]["stats"][f"{stat}"]["value"]-10)/2)

    update.message.reply_text('type your One Unique Thing\n')
    return ONE_UNIQUE_THING


def new_pc_one_unique_thing(update: Update, context: CallbackContext):
    """saves the O-U-T. Builds background keyboard"""
    user_id = update.effective_user.name
    pc_out = update.message.text

    global tmp_user_data
    tmp_user_data[f"{user_id}"]["tmp_character"]["one_unique_thing"] = pc_out

    # building background keyboard
    with open("json_files/classes.json", "r") as fp:
        pc_class_info = json.load(fp)[tmp_user_data[f"{user_id}"]["tmp_character"]["class"]]

    tmp_user_data[f"{user_id}"]["background_list"] = []
    reply_keyboard = []

    for background in pc_class_info["background"]:
        tmp_user_data[f"{user_id}"]["background_list"].append(background)
        reply_keyboard.append([background])
    update.message.reply_text(
        f'Please choose one background\n',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='choose stat'
        ),
    )

    return BACKGROUND_POINTS


def new_pc_background_points(update: Update, context: CallbackContext):
    """saves background and builds background points keyboard until points reach 0"""
    user_id = update.effective_user.name
    pc_background = update.message.text

    global tmp_user_data
    tmp_user_data[f"{user_id}"]["tmp_character"]["backgrounds"][f"{pc_background}"] = 0
    tmp_user_data[f"{user_id}"]["background_list"].remove(f"{pc_background}")

    if tmp_user_data[f"{user_id}"]["background_points"] > 0:
        # building points keyboard
        reply_keyboard = []
        for i in range(1, min(6, tmp_user_data[f"{user_id}"]["background_points"]+1)):
            reply_keyboard.append([i])
        update.message.reply_text(
            f'Please choose how many points to assign to {pc_background}\n',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder='choose points'
            ),
        )
    return BACKGROUND


def new_pc_background(update: Update, context: CallbackContext):
    """saves background points and builds background keyboard, until points reach 0"""
    user_id = update.effective_user.name
    pc_background_points = int(update.message.text)

    global tmp_user_data
    # adding points to background
    for background in tmp_user_data[f"{user_id}"]["tmp_character"]["backgrounds"].keys():
        if tmp_user_data[f"{user_id}"]["tmp_character"]["backgrounds"][f"{background}"] == 0:
            tmp_user_data[f"{user_id}"]["tmp_character"]["backgrounds"][f"{background}"] = pc_background_points
            break # BOLCHINI SCUSA NON HO VOGLIA DI FARLO PER BENE
    tmp_user_data[f"{user_id}"]["background_points"] -= pc_background_points

    if tmp_user_data[f"{user_id}"]["background_points"] > 0:
        # building background keyboard
        reply_keyboard = []
        for background in tmp_user_data[f"{user_id}"]["background_list"]:
            reply_keyboard.append([background])
        update.message.reply_text(
            f'Please choose one background\n',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder='choose background'
            ),
        )
        return BACKGROUND_POINTS
    # building keyboard for armor choice
    reply_keyboard = []
    with open("json_files/classes.json", "r") as fp:
        pc_class_info = json.load(fp)[f"{tmp_user_data[f'{user_id}']['tmp_character']['class']}"]
    for armor in pc_class_info["armor"].keys():
        reply_keyboard.append([armor])

    update.message.reply_text(
        f'Please choose your armor type\n',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='choose armor'
        ),
    )
    return ARMOR


def new_pc_armor_choice(update: Update, context: CallbackContext):
    """saves armor choice and builds melee weapon choice"""
    user_id = update.effective_user.name
    pc_armor = update.message.text

    global tmp_user_data
    with open("json_files/classes.json", "r") as fp:
        pc_class_info = json.load(fp)[f"{tmp_user_data[f'{user_id}']['tmp_character']['class']}"]

    # saving base ac value
    tmp_user_data[f"{user_id}"]["tmp_character"]["armor_class"] = pc_class_info["armor"][f"{pc_armor}"]

    # building melee weapon choice keyboard


    reply_keyboard = []
    for melee in pc_class_info["melee_weapon"]:
        reply_keyboard.append([melee])

    update.message.reply_text(
        f'Please choose your melee weapon\n',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='choose weapon'
        ),
    )
    return MELEE


def new_pc_melee_choice(update: Update, context: CallbackContext):
    """saves melee weapon choice and builds ranged weapon keyboard"""
    user_id = update.effective_user.name
    pc_melee_weapon = update.message.text

    global tmp_user_data

    # saving base ac value
    tmp_user_data[f"{user_id}"]["tmp_character"]["equipment"].append(pc_melee_weapon)

    # building ranged weapon choice keyboard
    with open("json_files/classes.json", "r") as fp:
        pc_class_info = json.load(fp)[f"{tmp_user_data[f'{user_id}']['tmp_character']['class']}"]

    reply_keyboard = []
    for ranged in pc_class_info["ranged_weapon"]:
        reply_keyboard.append([ranged])

    update.message.reply_text(
        f'Please choose your ranged weapon\n',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='choose weapon'
        ),
    )
    return RANGED


def new_pc_ranged_choice(update: Update, context: CallbackContext):
    """saves ranged weapon choice and builds icon selection keyboard"""
    user_id = update.effective_user.name
    pc_ranged_weapon = update.message.text

    global tmp_user_data

    # saving base ac value
    tmp_user_data[f"{user_id}"]["tmp_character"]["equipment"].append(pc_ranged_weapon)

    # building icon keyboard
    with open("json_files/icons.json", "r") as fp:
        icon_list = json.load(fp)["icons"]
    # saving icon list in tmp data structure
    tmp_user_data[f"{user_id}"]["icon_list"] = icon_list

    reply_keyboard = []
    for icon in icon_list:
        reply_keyboard.append([icon])

    update.message.reply_text(
        f'Please choose one icon\n',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='choose icon'
        ),
    )
    return ICON


def new_pc_icon_choice(update: Update, context: CallbackContext):
    """saves icon choice and builds icon relationship keyboard"""
    user_id = update.effective_user.name
    pc_icon = update.message.text

    global tmp_user_data

    # saving icon
    tmp_user_data[f"{user_id}"]["tmp_character"]["icon_relationships"][f"{pc_icon}"] = {}
    # removing icon from list of possible choices
    tmp_user_data[f"{user_id}"]["icon_list"].remove(f"{pc_icon}")

    # building keyboard for relationship
    reply_keyboard = [["positive relationship"],
                      ["conflicted relationship"],
                      ["negative relationship"]]

    update.message.reply_text(
        f'Please choose your relationship with {pc_icon}\n',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='choose relationship'
        ),
    )

    return ICON_RELATIONSHIP


def new_pc_icon_relationship(update: Update, context: CallbackContext):
    """saves icon relationship choice and builds icon points keyboard"""
    user_id = update.effective_user.name
    pc_icon_relationship = update.message.text

    global tmp_user_data

    # saving in tmp data structure
    for icon in tmp_user_data[f"{user_id}"]["tmp_character"]["icon_relationships"].keys():
        if len(tmp_user_data[f"{user_id}"]["tmp_character"]["icon_relationships"][f"{icon}"].keys()) == 0:
            tmp_user_data[f"{user_id}"]["tmp_character"]["icon_relationships"][f"{icon}"]["relationship"] = f"{pc_icon_relationship}"

    # building keyboard for relationship points
    remaining_relationship_points = tmp_user_data[f"{user_id}"]["icon_relationship_points"]
    reply_keyboard = []
    for i in range(1, min(4, remaining_relationship_points+1)):
        reply_keyboard.append([i])

    update.message.reply_text(
        f'Please choose your relationship points with this icon\n',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='choose points'
        ),
    )
    return ICON_RELATIONSHIP_POINTS


def new_pc_icon_points(update: Update, context: CallbackContext):
    """saves icon points. Until points reach 0, it builds icon keyboard again.
    When points reach 0, saves the finished character on json and ends conversation"""
    user_id = update.effective_user.name
    pc_icon_relationship_points = int(update.message.text)

    global tmp_user_data

    #saving points
    for icon in tmp_user_data[f"{user_id}"]["tmp_character"]["icon_relationships"].keys():
        if len(tmp_user_data[f"{user_id}"]["tmp_character"]["icon_relationships"][f"{icon}"].keys()) == 1:
            tmp_user_data[f"{user_id}"]["tmp_character"]["icon_relationships"][f"{icon}"]["points"] =\
                pc_icon_relationship_points
    tmp_user_data[f"{user_id}"]["icon_relationship_points"] -= pc_icon_relationship_points

    if tmp_user_data[f"{user_id}"]["icon_relationship_points"] > 0:
        # rebuilding icon list keyboard
        reply_keyboard = []
        for icon in tmp_user_data[f"{user_id}"]["icon_list"]:
            reply_keyboard.append([icon])

        update.message.reply_text(
            f'Please choose one icon\n',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder='choose icon'
            ),
        )
        return ICON

    # computing combined stats, saving on file
    new_pc_stats_compute(user_id)
    update.message.reply_text("character succesfully created!\n")

    return ConversationHandler.END


def new_pc_stats_compute(user_id: str):
    """computes every combined stat, and saves the created character onto the json file"""
    global tmp_user_data

    # hp computation
    tmp_user_data[f"{user_id}"]["tmp_character"]["hit_points"] = \
        3*(tmp_user_data[f"{user_id}"]["tmp_character"]["hit_points"] +
           tmp_user_data[f"{user_id}"]["tmp_character"]["stats"]["con"]["modifier"])

    # ac computation
    tmp_user_data[f"{user_id}"]["tmp_character"]["armor_class"] =\
        tmp_user_data[f"{user_id}"]["tmp_character"]["armor_class"] + \
        uf.middle(tmp_user_data[f"{user_id}"]["tmp_character"]["stats"]["con"]["modifier"],
                  tmp_user_data[f"{user_id}"]["tmp_character"]["stats"]["dex"]["modifier"],
                  tmp_user_data[f"{user_id}"]["tmp_character"]["stats"]["wis"]["modifier"])\
        + 1

    # physical defense computation
    tmp_user_data[f"{user_id}"]["tmp_character"]["physical_defense"] =\
        tmp_user_data[f"{user_id}"]["tmp_character"]["physical_defense"] + \
        uf.middle(tmp_user_data[f"{user_id}"]["tmp_character"]["stats"]["str"]["modifier"],
                  tmp_user_data[f"{user_id}"]["tmp_character"]["stats"]["con"]["modifier"],
                  tmp_user_data[f"{user_id}"]["tmp_character"]["stats"]["dex"]["modifier"])\
        + 1

    # mental defense computation
    tmp_user_data[f"{user_id}"]["tmp_character"]["mental_defense"] =\
        tmp_user_data[f"{user_id}"]["tmp_character"]["mental_defense"] + \
        uf.middle(tmp_user_data[f"{user_id}"]["tmp_character"]["stats"]["int"]["modifier"],
                  tmp_user_data[f"{user_id}"]["tmp_character"]["stats"]["wis"]["modifier"],
                  tmp_user_data[f"{user_id}"]["tmp_character"]["stats"]["cha"]["modifier"])\
        + 1

    # initiative bonus
    tmp_user_data[f"{user_id}"]["tmp_character"]["initiative"] =\
        tmp_user_data[f"{user_id}"]["tmp_character"]["stats"]["dex"]["modifier"] + 1

    # saving character in json file
    with open(f"json_files/users/{user_id}.json", "r") as fp:
        user_info = json.load(fp)
    # name conversion into lower case to standardize keys:
    pc_name_key = ("_".join(tmp_user_data[f'{user_id}']['tmp_character']['name'].split())).lower()
    user_info[f"{pc_name_key}"] = tmp_user_data[f"{user_id}"]["tmp_character"]

    with open(f"json_files/users/{user_id}.json", "w") as fp:
        json.dump(user_info, fp, indent=4)

    tmp_user_data.pop(f"{user_id}")


def help_f(update: Update, context: CallbackContext):
    """help message"""
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="A complete list of available commands is present as a suggestion on your telegram keyboard")


def roll(update: Update, context: CallbackContext):
    """
    /roll command handler. Supports multiple dice throws, modifier addiction/subtraction,
    and an inline keyboard mode
    """

    input_text = ''.join(context.args)
    # regex used for user input verification
    pattern_v3 = r"(?!ABC)(([1-9][0-9]*d[1-9][0-9]*)(,[1-9][0-9]*d[1-9][0-9]*)*)([\+|-][0-9]+)?(?<!ABC)"

    # inline keyboard mode
    if len(input_text) == 0:
        keyboard = [
            [
                InlineKeyboardButton("d4", callback_data="4"), InlineKeyboardButton("d6", callback_data="6")
            ],
            [
                InlineKeyboardButton("d8", callback_data="8"), InlineKeyboardButton("d12", callback_data="12")
            ],
            [
                InlineKeyboardButton("d20", callback_data="20"), InlineKeyboardButton("d100", callback_data="100")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Choose your dice roll", reply_markup=reply_markup)

    # text mode:
    elif re.fullmatch(pattern_v3, input_text):
        # dividing input into groups of dice rolls and modifier
        input_components = re.split(r'(\+|-)', input_text)
        roll_groups = input_components[0].split(',')

        result = 0
        roll_log = []
        for group in roll_groups:
            # input conversion (ex "1d6" -> 1, 6)
            entries = group.split(sep="d")
            rolls = int(entries[0])
            dice_type = int(entries[1])

            outcome = uf.dice_roll(rolls, dice_type)
            result += outcome['rolls_total']
            roll_log += outcome['rolls_log']

        if len(input_components) > 1:
            roll_modifier = int(input_components[2])
            if input_components[1] == '+':
                result += roll_modifier
            elif input_components[1] == '-':
                result -= roll_modifier

            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"{' + '.join(str(r) for r in roll_log)} ({input_components[1]}{roll_modifier}) = {result}")

        else:
            if len(roll_log) > 1:
                context.bot.send_message(chat_id=update.effective_chat.id, text=f"{' + '.join(roll_log)} = {result}")
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text=f"{result}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="invalid command arguments, retry")


def gui_dice_roll(update: Update, context: CallbackContext):

    """callback function for dice keyboard"""
    dice = int(update.callback_query.data)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"Result for d{dice}: {uf.dice_roll(1, dice)['rolls_total']}")

def save_currency(update: Update, context: CallbackContext):
    """gives currency to a character"""
    user_id = update.effective_user.name

    pattern = "^[^,]+,[0-9]+$"
    if not re.fullmatch(pattern, "".join(context.args)):
        update.message.reply_text("Correct usage:\n\"/save_currency <charachter name>, <quantity>\"")
        return

    input_text = (" ".join(context.args)).split(", ")
    pc_name = " ".join(input_text[0].split())
    pc = "_".join(input_text[0].lower().split())
    balance_modifier = input_text[1]

    correct_input = r"[0-9]*"

    try:
        with open(f"json_files/users/{user_id}.json", "r") as fp:
            user_data = json.load(fp)
            user_data_player = user_data[f"{pc}"]
    except KeyError:
        update.message.reply_text(f"You have no character named {pc_name}")
        return

    if re.fullmatch(correct_input, balance_modifier):
        user_data[f"{pc}"]["balance"] += int(balance_modifier)

        with open(f"json_files/users/{user_id}.json", "w") as fp:
            json.dump(user_data, fp, indent=4)

        update.message.reply_text(f"New balance: {user_data[f'{pc}']['balance']}")
    else:
        update.message.reply_text("aborted: enter a valid number")


def pay_currency(update: Update, context: CallbackContext):
    """takes currency from a character"""

    pattern = "^[^,]+,[0-9]+$"
    if not re.fullmatch(pattern, "".join(context.args)):
        update.message.reply_text("Correct usage:\n\"/pay_currency <charachter name>, <quantity>\"")
        return

    user_id = update.effective_user.name

    input_text = (" ".join(context.args)).split(", ")
    pc_name = " ".join(input_text[0].split())
    pc = "_".join(input_text[0].lower().split())
    balance_modifier = input_text[1]

    correct_input = r"[0-9]*"

    try:
        with open(f"json_files/users/{user_id}.json", "r") as fp:
            user_data = json.load(fp)
            user_data_player = user_data[f"{pc}"]
    except KeyError:
        update.message.reply_text(f"You have no character named {pc_name}")
        return

    if re.fullmatch(correct_input, balance_modifier):
        if user_data[f"{pc}"]["balance"] >= int(balance_modifier):
            user_data[f"{pc}"]["balance"] -= int(balance_modifier)

            with open(f"json_files/users/{user_id}.json", "w") as fp:
                json.dump(user_data, fp, indent=4)
            update.message.reply_text(f"New balance: {user_data[f'{pc}']['balance']}")
        else:
            update.message.reply_text("aborted: you can't spend money you don't have!")
    else:
        update.message.reply_text("aborted: enter a valid number")


def add_magic_item(update: Update, context: CallbackContext):
    """adds a magic item to a character inventory"""

    pattern = "^[^,]+,[^,]+$"
    if not re.fullmatch(pattern, "".join(context.args)):
        update.message.reply_text("Correct usage:\n\"/give_magic_item <charachter name>, <magic item>\"")
        return

    user_id = update.effective_user.name

    input_text = (" ".join(context.args)).split(", ")
    pc_name = " ".join(input_text[0].split())
    pc = "_".join(input_text[0].lower().split())
    new_magic_item = input_text[1]

    try:
        with open(f"json_files/users/{user_id}.json", "r") as fp:
            user_data = json.load(fp)
            user_data_player = user_data[f"{pc}"]
    except KeyError:
        update.message.reply_text(f"You have no character named {pc_name}!")
        return

    user_data[f"{pc}"]["magic_items"].append(new_magic_item)

    with open(f"json_files/users/{user_id}.json", "w") as fp:
        json.dump(user_data, fp, indent=4)

    update.message.reply_text(f"\"{new_magic_item}\" added to your inventory!")


def leave_magic_item(update: Update, context: CallbackContext):
    """Takes a magic item from a character inventory"""

    pattern = "^[^,]+,[^,]+$"
    if not re.fullmatch(pattern, "".join(context.args)):
        update.message.reply_text("Correct usage:\n\"/leave_magic_item <charachter name>, <magic item>\"")
        return

    user_id = update.effective_user.name

    input_text = (" ".join(context.args)).split(", ")
    pc_name = " ".join(input_text[0].split())
    pc = "_".join(input_text[0].lower().split())
    removable_magic_item = input_text[1]

    try:
        with open(f"json_files/users/{user_id}.json", "r") as fp:
            user_data = json.load(fp)
            user_data_player = user_data[f"{pc}"]
    except KeyError:
        update.message.reply_text(f"You have no character named {pc_name}!")
        return

    try:
        user_data[f"{pc}"]["magic_items"].remove(removable_magic_item)

        with open(f"json_files/users/{user_id}.json", "w") as fp:
            json.dump(user_data, fp, indent=4)

        update.message.reply_text(f"\"{removable_magic_item}\" removed from your inventory!")

    except ValueError:
        update.message.reply_text( f"you don't have \"{removable_magic_item}\" in your inventory!")


def add_item(update: Update, context: CallbackContext):
    """
    Adds the specified item to the player list
    input_text[0]: player name
    input_text[1]: item
    """

    pattern = "^[^,]+,[^,]+$"
    if not re.fullmatch(pattern, "".join(context.args)):
        update.message.reply_text("Correct usage:\n\"/give_item <charachter name>, <item>\"")
        return

    user_id = update.effective_user.name

    input_text = (" ".join(context.args)).split(", ")
    pc_name = " ".join(input_text[0].split())
    pc = "_".join(input_text[0].lower().split())
    new_item = input_text[1]

    try:
        with open(f"json_files/users/{user_id}.json", "r") as fp:
            user_data = json.load(fp)
            user_data_player = user_data[f"{pc}"]
    except KeyError:
        update.message.reply_text(f"You have no character named {pc_name}!")
        return

    user_data[f"{pc}"]["equipment"].append(new_item)

    with open(f"json_files/users/{user_id}.json", "w") as fp:
        json.dump(user_data, fp, indent=4)

    update.message.reply_text(f"\"{new_item}\" added to your inventory!")


def leave_item(update: Update, context: CallbackContext):
    """Takes an item from a character inventory"""


    pattern = "^[^,]+,[^,]+$"
    if not re.fullmatch(pattern, "".join(context.args)):
        update.message.reply_text("Correct usage:\n\"/leave_item <charachter name>, <item>\"")
        return

    user_id = update.effective_user.name

    input_text = (" ".join(context.args)).split(", ")
    pc_name = " ".join(input_text[0].split())
    pc = "_".join(input_text[0].lower().split())
    removable_item = input_text[1]

    # adding new item
    try:
        with open(f"json_files/users/{user_id}.json", "r") as fp:
            user_data = json.load(fp)
            user_data_player = user_data[f"{pc}"]
    except KeyError:
        update.message.reply_text(f"You have no character named {pc_name}")
        return

    try:
        user_data[f"{pc}"]["equipment"].remove(removable_item)

        with open(f"json_files/users/{user_id}.json", "w") as fp:
            json.dump(user_data, fp, indent=4)

        update.message.reply_text(f"\"{removable_item}\" removed from your inventory!")

    except ValueError:
        update.message.reply_text(f"you don't have \"{removable_item}\" in your inventory!")


def get_player_sheet(update: Update, context: CallbackContext):
    """prints a character sheet"""

    pattern = ".+"
    if not re.fullmatch(pattern, "".join(context.args)):
        update.message.reply_text("Correct usage:\n\"/get_sheet <charachter name>\"")
        return

    user_id = update.effective_user.name
    pc_name = " ".join(context.args)
    pc_name_key = "_".join(context.args).lower()

    with open(f"json_files/users/{user_id}.json", "r") as fp:
        try:
            user_data = json.load(fp)[f"{pc_name_key}"]
            update.message.reply_text(f"{json.dumps(user_data, indent=4)}")
        except KeyError:
            update.message.reply_text(f"You have no character named {pc_name}!")


def unknown(update: Update, context: CallbackContext):
    """error message for unrecognized commands"""
    context.bot.send_message(chat_id=update.effective_chat.id, text='Unknown command, try /help')


if __name__ == "__main__":
    main()
