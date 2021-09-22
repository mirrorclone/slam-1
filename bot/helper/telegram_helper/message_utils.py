from telegram import InlineKeyboardMarkup
from telegram.message import Message
from telegram.update import Update
import psutil, shutil
import time
from bot import AUTO_DELETE_MESSAGE_DURATION, LOGGER, bot, \
    status_reply_dict, status_reply_dict_lock, download_dict, download_dict_lock, botStartTime, Interval, DOWNLOAD_STATUS_UPDATE_INTERVAL
from bot.helper.ext_utils.bot_utils import get_readable_message, get_readable_file_size, get_readable_time, MirrorStatus, setInterval
from telegram.error import TimedOut, BadRequest


def sendMessage(text: str, bot, update: Update):
    try:
        return bot.send_message(update.message.chat_id,
                            reply_to_message_id=update.message.message_id,
                            text=text, allow_sending_without_reply=True,  parse_mode='HTMl')
    except Exception as e:
        LOGGER.error(str(e))
def sendMarkup(text: str, bot, update: Update, reply_markup: InlineKeyboardMarkup):
    return bot.send_message(update.message.chat_id,
                            reply_to_message_id=update.message.message_id,
                            text=text, reply_markup=reply_markup, allow_sending_without_reply=True, parse_mode='HTMl')

def editMessage(text: str, message: Message, reply_markup=None):
    try:
        bot.edit_message_text(text=text, message_id=message.message_id,
                              chat_id=message.chat.id,reply_markup=reply_markup,
                              parse_mode='HTMl')
    except Exception as e:
        LOGGER.error(str(e))


def deleteMessage(bot, message: Message):
    try:
        bot.delete_message(chat_id=message.chat.id,
                           message_id=message.message_id)
    except Exception as e:
        LOGGER.error(str(e))


def sendLogFile(bot, update: Update):
    with open('log.txt', 'rb') as f:
        bot.send_document(document=f, filename=f.name,
                          reply_to_message_id=update.message.message_id,
                          chat_id=update.message.chat_id)


def auto_delete_message(bot, cmd_message: Message, bot_message: Message):
    if AUTO_DELETE_MESSAGE_DURATION != -1:
        time.sleep(AUTO_DELETE_MESSAGE_DURATION)
        try:
            # Skip if None is passed meaning we don't want to delete bot xor cmd message
            deleteMessage(bot, cmd_message)
            deleteMessage(bot, bot_message)
        except AttributeError:
            pass


def delete_all_messages():
    with status_reply_dict_lock:
        for message in list(status_reply_dict.values()):
            try:
                deleteMessage(bot, message)
                del status_reply_dict[message.chat.id]
            except Exception as e:
                LOGGER.error(str(e))


def update_all_messages():
    total, used, free = shutil.disk_usage('.')
    free = get_readable_file_size(free)
    msg, buttons = get_readable_message()
    msg += f"\n<b>💽 ғʀᴇᴇ:</b> {free}\n"
    with status_reply_dict_lock:
        for chat_id in list(status_reply_dict.keys()):
            if status_reply_dict[chat_id] and msg != status_reply_dict[chat_id].text:
                try:
                    if buttons == "":
                        editMessage(msg, status_reply_dict[chat_id])
                    else:
                        editMessage(msg, status_reply_dict[chat_id], buttons)
                except Exception as e:
                    LOGGER.error(str(e))
                status_reply_dict[chat_id].text = msg


def sendStatusMessage(msg, bot):
    if len(Interval) == 0:
        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))
    total, used, free = shutil.disk_usage('.')
    free = get_readable_file_size(free)
    progress, buttons = get_readable_message()
    if progress is None:
        progress, buttons = get_readable_message()
    progress += f"\n<b>💽 ғʀᴇᴇ:</b> {free}\n"
    with status_reply_dict_lock:
        if msg.message.chat.id in list(status_reply_dict.keys()):
            try:
                message = status_reply_dict[msg.message.chat.id]
                deleteMessage(bot, message)
                del status_reply_dict[msg.message.chat.id]
            except Exception as e:
                LOGGER.error(str(e))
                del status_reply_dict[msg.message.chat.id]
        if buttons == "":
            message = sendMessage(progress, bot, msg)
        else:
            message = sendMarkup(progress, bot, msg, buttons)
        status_reply_dict[msg.message.chat.id] = message
