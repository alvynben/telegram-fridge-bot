#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

import logging
from typing import Tuple, Dict, Any

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackQueryHandler,
    CallbackContext,
)

# import BOT API key from config.py in same directory
import config

# State definitions for top level conversation
SELECTING_ACTION, ADD_ITEM, CHANGE_ITEM, DESCRIBING_SELF = map(chr, range(4))
# State definitions for second level conversation
SELECTING_LABEL, SELECTING_EXPIRY, SELECTING_QTY = map(chr, range(4, 7))
# State definitions for descriptions conversation
SELECTING_FEATURE, TYPING = map(chr, range(7, 9))
# Meta states
STOPPING, SHOWING = map(chr, range(9, 11))
# Shortcut for ConversationHandler.END
END = ConversationHandler.END

# Different constants for this example
(
    FREEZER_TOP,
    FREEZER_BOTTOM,
    FREEZER_SIDE,
    CHILLER,
    FRIDGE_TOP,
    FRIDGE_BOTTOM,
    FRIDGE_SIDE,
    VEG_AREA,
    ITEM,
    LABEL,
    EXPIRY,
    QTY,
    START_OVER,
    FEATURES,
    CURRENT_FEATURE,
    CURRENT_LEVEL,
    DESCRIBING_ITEM,
    ADDING_ITEM,
    CURRENT_LOCATION,
    CURRENT_ITEM,
    DONE,
    CHANGING_ITEM,
    EDIT_ITEM,
    PURPOSE,
    REMOVE,
) = map(chr, range(11, 36))

# Text for respective characters

constant_to_location = {
    FREEZER_TOP: "Freezer Top",
    FREEZER_BOTTOM: "Freezer Bottom",
    FREEZER_SIDE: "Freezer Side",
    CHILLER: "Chiller",
    FRIDGE_TOP: "Fridge Top",
    FRIDGE_BOTTOM: "Fridge Bottom",
    FRIDGE_SIDE: "Fridge Side",
    VEG_AREA: "Veg Area",
}

constant_to_feature = {LABEL: "Label", QTY: "Quantity", EXPIRY: "Expiry"}


def start(update: Update, context: CallbackContext) -> str:
    """Select an action: Add item, change item, or show store"""
    text = "You may choose to add an item, change the quantity of a stored item, or end the conversation. To abort, simply type /stop."

    buttons = [
        [
            InlineKeyboardButton(text="Add item", callback_data=str(ADD_ITEM)),
            InlineKeyboardButton(
                text="Change item", callback_data=str(CHANGE_ITEM)
            ),
        ],
        [
            InlineKeyboardButton(text="Show store", callback_data=str(SHOWING)),
            InlineKeyboardButton(text="Done", callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we're starting over, we don't need to send a new message
    if context.user_data.get(START_OVER):
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    else:
        update.message.reply_text("Hey, I'm your fridge, honey! What do you wanna do?")
        update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False

    return SELECTING_ACTION


def adding_item(update: Update, context: CallbackContext) -> str:
    """Add an item into the fridge."""

    context.user_data[CURRENT_LOCATION] = update.callback_query.data
    text = "Okay, please describe your entry."
    buttons = [
        [
            InlineKeyboardButton(text="Add label", callback_data=str(LABEL)),
            InlineKeyboardButton(text="Add expiry", callback_data=str(EXPIRY)),
        ],
        [
            InlineKeyboardButton(text="Add quantity", callback_data=str(QTY)),
            InlineKeyboardButton(text="Done", callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return SELECTING_FEATURE


def ask_for_input(update: Update, context: CallbackContext) -> str:
    """Ask for item details."""

    user_data = context.user_data
    user_data[CURRENT_FEATURE] = update.callback_query.data
    text = f"Type out the {constant_to_feature[user_data[CURRENT_FEATURE]]}!"

    if user_data[PURPOSE] == CHANGE_ITEM:
        item = user_data[user_data[CURRENT_LOCATION]][int(user_data[CURRENT_ITEM])]
        text += f"\nCurrent Item: \n{item[LABEL]} | {item[QTY]} | {item[EXPIRY]}"
    elif user_data[PURPOSE] == ADD_ITEM:
        if user_data.get(FEATURES):
            item = user_data[FEATURES]
        else:
            user_data[FEATURES] = {LABEL: "N.A.", QTY: "N.A.", EXPIRY: "N.A."}
            item = user_data[FEATURES]
        text += f"\nCurrent Item: \n{item[LABEL]} | {item[QTY]} | {item[EXPIRY]}"

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)

    return TYPING


def save_input(update: Update, context: CallbackContext) -> str:
    """Save item details"""
    user_data = context.user_data
    if not user_data.get(FEATURES):
        user_data[FEATURES] = {}
    user_data[FEATURES][user_data[CURRENT_FEATURE]] = update.message.text

    text = "Okay, please describe your entry."
    if user_data[PURPOSE] == CHANGE_ITEM:
        item = user_data[user_data[CURRENT_LOCATION]][int(user_data[CURRENT_ITEM])]
        text += f"\nCurrent Item: \n{item[LABEL]} | {item[QTY]} | {item[EXPIRY]}"
        buttons = [
            [
                InlineKeyboardButton(text="Change label", callback_data=str(LABEL)),
                InlineKeyboardButton(text="Change expiry", callback_data=str(EXPIRY)),
            ],
            [
                InlineKeyboardButton(text="Change quantity", callback_data=str(QTY)),
                InlineKeyboardButton(text="Done", callback_data=str(END)),
            ],
        ]
    elif user_data[PURPOSE] == ADD_ITEM:
        item = user_data[FEATURES]
        text += f"\nCurrent Item: \n{item[LABEL]} | {item[QTY]} | {item[EXPIRY]}"
        buttons = [
            [
                InlineKeyboardButton(text="Add label", callback_data=str(LABEL)),
                InlineKeyboardButton(text="Add expiry", callback_data=str(EXPIRY)),
            ],
            [
                InlineKeyboardButton(text="Add quantity", callback_data=str(QTY)),
                InlineKeyboardButton(text="Done", callback_data=str(END)),
            ],
        ]
    keyboard = InlineKeyboardMarkup(buttons)

    update.message.reply_text(text=text, reply_markup=keyboard)

    return SELECTING_FEATURE


def end_describing(update: Update, context: CallbackContext) -> str:
    """End gathering of features and return to parent conversation."""
    user_data = context.user_data
    item = user_data[FEATURES].copy()
    location = user_data[CURRENT_LOCATION]
    purpose = user_data[PURPOSE]

    if purpose == ADD_ITEM:
        if not user_data.get(location):
            user_data[location] = []
        user_data[location].append(item)
    elif purpose == CHANGE_ITEM:
        user_data[location][int(user_data[CURRENT_ITEM])] = item

    # Clear item's temporary info cache after saving
    user_data[FEATURES] = {}    

    text = "Item saved! What's next?"
    buttons = [
        [
            InlineKeyboardButton(text="Add item", callback_data=str(ADD_ITEM)),
            InlineKeyboardButton(text="Change item", callback_data=str(CHANGE_ITEM)),
        ],
        [
            InlineKeyboardButton(text="Show store", callback_data=str(SHOWING)),
            InlineKeyboardButton(text="Done", callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return DONE


def stop(update: Update, context: CallbackContext) -> int:
    """End Conversation by command."""
    try:
        update.message.reply_text("Okay, bye.")
    except:
        update.callback_query.edit_message_text(text="Okay, bye.")
    
    context.user_data[START_OVER] = False

    return END


def show_data(update: Update, context: CallbackContext) -> str:
    """Pretty print gathered data."""

    def prettyprint(user_data: Dict[str, Any], location: str) -> str:

        items = user_data.get(location)
        if not items:
            return f"\n{constant_to_location[location]}:\nNo information yet."

        text = ""

        text += "\n" + constant_to_location[location] + ":"

        for item in user_data[location]:
            text += f"\n{item[LABEL]} | {item[QTY]} | {item[EXPIRY]}"

        text += "\n"

        return text

    user_data = context.user_data

    locations = {
        FREEZER_TOP,
        FREEZER_BOTTOM,
        FREEZER_SIDE,
        CHILLER,
        FRIDGE_TOP,
        FRIDGE_BOTTOM,
        FRIDGE_SIDE,
        VEG_AREA,
    }

    text = ""
    for location in locations:
        text += prettyprint(user_data, location) + "\n\n"

    buttons = [[InlineKeyboardButton(text="Back", callback_data=str(END))]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    user_data[START_OVER] = True

    return SHOWING


def choosing_location(update: Update, context: CallbackContext) -> str:

    purpose = update.callback_query.data
    user_data = context.user_data

    if purpose == ADD_ITEM:
        text = "Okay, where would you like to place the item?"
        user_data[PURPOSE] = ADD_ITEM
    elif purpose == CHANGE_ITEM:
        text = "Alright, where is the item you'd like to move?"
        user_data[PURPOSE] = CHANGE_ITEM

    buttons = [
        [
            InlineKeyboardButton(text="Freezer Top", callback_data=str(FREEZER_TOP)),
            InlineKeyboardButton(text="Freezer Side", callback_data=str(FREEZER_SIDE)),
        ],
        [
            InlineKeyboardButton(
                text="Freezer Bottom", callback_data=str(FREEZER_BOTTOM)
            ),
            InlineKeyboardButton(text="Freezer Side", callback_data=str(FREEZER_SIDE)),
        ],
        [
            InlineKeyboardButton(text="Chiller", callback_data=str(CHILLER)),
        ],
        [
            InlineKeyboardButton(text="Fridge Top", callback_data=str(FRIDGE_TOP)),
            InlineKeyboardButton(text="Fridge Side", callback_data=str(FRIDGE_SIDE)),
        ],
        [
            InlineKeyboardButton(
                text="Fridge Bottom", callback_data=str(FRIDGE_BOTTOM)
            ),
            InlineKeyboardButton(text="Fridge Side", callback_data=str(FRIDGE_SIDE)),
        ],
        [
            InlineKeyboardButton(text="Veg Area", callback_data=str(VEG_AREA)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    if purpose == ADD_ITEM:
        return ADDING_ITEM
    elif purpose == CHANGE_ITEM:
        return CHANGING_ITEM


def choosing_item(update: Update, context: CallbackContext) -> str:

    user_data = context.user_data
    user_data[CURRENT_LOCATION] = update.callback_query.data
    buttons = []

    if not user_data.get(user_data[CURRENT_LOCATION]):
        text = "No items present!"
        buttons.append([InlineKeyboardButton(text="Back", callback_data=str(END))])
        keyboard = InlineKeyboardMarkup(buttons)
    else:
        items = user_data[user_data[CURRENT_LOCATION]]
        for i in range(len(items)):
            item = items[i]
            button = [
                InlineKeyboardButton(
                    text=f"\n{item[LABEL]} | {item[QTY]} | {item[EXPIRY]}",
                    callback_data=str(i),
                )
            ]
            buttons.append(button)
        buttons.append([InlineKeyboardButton(text="Back", callback_data=str(END))])
        keyboard = InlineKeyboardMarkup(buttons)
        text = "Choose your item!"
    
    user_data[START_OVER] = True
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return EDIT_ITEM


def edit_item(update: Update, context: CallbackContext) -> str:

    user_data = context.user_data
    user_data[CURRENT_ITEM] = update.callback_query.data
    item = user_data[user_data[CURRENT_LOCATION]][int(user_data[CURRENT_ITEM])]
    user_data[FEATURES] = item

    text = f"Okay, what would you like to change about:\n{item[LABEL]} | {item[QTY]} | {item[EXPIRY]}"
    buttons = [
        [
            InlineKeyboardButton(text="Change label", callback_data=str(LABEL)),
            InlineKeyboardButton(text="Change expiry", callback_data=str(EXPIRY)),
        ],
        [
            InlineKeyboardButton(text="Change quantity", callback_data=str(QTY)),
            InlineKeyboardButton(text="Remove", callback_data=str(REMOVE)),
        ],
        [InlineKeyboardButton(text="Done", callback_data=str(END))],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return SELECTING_FEATURE


def remove_item(update: Update, context: CallbackContext) -> str:
    user_data = context.user_data
    user_data[user_data[CURRENT_LOCATION]].pop(int(float(user_data[CURRENT_ITEM])))

    text = "Item deleted! What's next?"
    buttons = [
        [
            InlineKeyboardButton(text="Add item", callback_data=str(ADD_ITEM)),
            InlineKeyboardButton(text="Change item", callback_data=str(CHANGE_ITEM)),
        ],
        [
            InlineKeyboardButton(text="Show store", callback_data=str(SHOWING)),
            InlineKeyboardButton(text="Done", callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return DONE


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(config.bot_api_key)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    choosing_location_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(choosing_location, pattern="^" + str(ADD_ITEM) + "$"),
            CallbackQueryHandler(
                choosing_location, pattern="^" + str(CHANGE_ITEM) + "$"
            ),
        ],
        states={
            ADDING_ITEM: [
                CallbackQueryHandler(adding_item, pattern="^(?!" + str(END) + ").*$")
            ],
            CHANGING_ITEM: [
                CallbackQueryHandler(choosing_item, pattern="^(?!" + str(END) + ").*$")
            ],
            EDIT_ITEM: [
                CallbackQueryHandler(edit_item, pattern="^(?!" + str(END) + ").*$"),
                CallbackQueryHandler(start, pattern="^" + str(END) + "$"),
            ],
            SELECTING_FEATURE: [
                CallbackQueryHandler(ask_for_input, pattern="^(?!" + "(" + str(END) + "|" + str(REMOVE) +")" + ").*$"),
                CallbackQueryHandler(remove_item, pattern="^" + str(REMOVE) + "$"),
            ],
            TYPING: [MessageHandler(Filters.text & ~Filters.command, save_input)],
        },
        fallbacks=[
            CallbackQueryHandler(end_describing, pattern="^" + str(END) + "$"),
        ],
        map_to_parent={
            DONE: SELECTING_ACTION,
            SELECTING_ACTION: SELECTING_ACTION
        },
    )

    selection_handlers = [
        choosing_location_conv,
        CallbackQueryHandler(show_data, pattern="^" + str(SHOWING) + "$"),
        CallbackQueryHandler(stop, pattern="^" + str(END) + "$"),
    ]

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SHOWING: [CallbackQueryHandler(start, pattern="^" + str(END) + "$")],
            SELECTING_ACTION: selection_handlers,
            STOPPING: [CommandHandler("start", start)],
        },
        fallbacks=[CommandHandler("stop", stop)],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()
