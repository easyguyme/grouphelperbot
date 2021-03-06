﻿import telepot, time
from tinydb import TinyDB, where
db_users = TinyDB('users.json')
db_admins = TinyDB('admins.json')


def initialize():
    try:
        f = open("bot_token.txt", "r")
        token = str(f.readline())
        bot = telepot.Bot(token)
        f.close()
    except FileNotFoundError:
        f = open("bot_token.txt", "w")
        token = str(input("Token File not found. Please insert the HTTP API Bot Token: "))
        bot = telepot.Bot(token)
        f.write(token)
        f.close()
    try:
        f = open("group_id.txt", "r")
        group = int(f.readline())
        f.close()
    except FileNotFoundError:
        f = open("group_id.txt", "w")
        group = int(input("Group ID File not found. Please insert the group Chat ID: "))
        f.write(str(group))
        f.close()

    groupUserCount = bot.getChatMembersCount(group)
    myusername = "@" + bot.getMe()['username']
    print("Bot started...")
    return bot, group, groupUserCount, myusername


def reloadAdmins():
    for x in bot.getChatAdministrators(group):
        if x['user']['is_bot']:
            updateAdminDatabase(x['user']['id'], "bot")
        elif x['status'] == "administrator":
            updateAdminDatabase(x['user']['id'], "admin")
        elif x['status'] == "creator":
            updateAdminDatabase(x['user']['id'], "creator")


def updateAdminDatabase(id, status):
    if db_admins.search(where('chatId') == id):
        db_admins.update({'status': status}, where('chatId') == id)
    else:
        db_admins.insert({'chatId': id, 'status': status})


def updateUserDatabase(id, firstName, lastName, username):
    if db_users.search(where('chatId') == id):
        db_users.update({'firstName': firstName, 'lastName': lastName, 'username': username}, where('chatId') == id)
    else:
        db_users.insert({'chatId': id, 'firstName': firstName, 'lastName': lastName, 'username': username, 'warns': "0"})


def getUserInfo(msg):
    chatId = int(msg['chat']['id'])
    msgId = int(msg['message_id'])
    from_id = int(msg['from']['id'])

    try:
        text = str(msg['text'])
    except KeyError:
        text = ""
    try:
        from_firstName = str(msg['from']['first_name'])
    except KeyError:
        from_firstName = ""
    try:
        from_lastName = str(msg['from']['last_name'])
    except KeyError:
        from_lastName = ""
    try:
        from_username = str(msg['from']['username'])
    except KeyError:
        from_username = ""

    try:
        x = msg['reply_to_message']
        isReply = True
        reply_msgId = int(msg['reply_to_message']['message_id'])
        reply_fromId = int(msg['reply_to_message']['from']['id'])
        try:
            reply_firstName = str(msg['reply_to_message']['from']['first_name'])
        except KeyError:
            reply_firstName = ""
        try:
            reply_lastName = str(msg['reply_to_message']['from']['last_name'])
        except KeyError:
            reply_lastName = ""
        try:
            reply_username = str(msg['reply_to_message']['from']['username'])
        except KeyError:
            reply_username = ""

    except KeyError:
        isReply = False
        reply_msgId = None
        reply_fromId = None
        reply_firstName = None
        reply_lastName = None
        reply_username = None


    return chatId, msgId, text, from_id, from_firstName, from_lastName, from_username, isReply, reply_msgId, reply_fromId, reply_firstName, reply_lastName, reply_username


def isAdmin(chatId):
    if chatId in [x["chatId"] for x in db_admins.search(where('status') == "admin")]:
        return True
    elif chatId in [x["chatId"] for x in db_admins.search(where('status') == "creator")]:
        return True
    else:
        return False


def handle(msg):
    chatId, msgId, text, from_id, from_firstName, from_lastName, from_username, isReply, reply_msgId, reply_fromId, reply_firstName, reply_lastName, reply_username = getUserInfo(msg)
    global groupUserCount

    if chatId == group:
        updateUserDatabase(from_id, from_firstName, from_lastName, from_username)

        # Welcoming message
        if bot.getChatMembersCount(group) > groupUserCount:
            bot.sendMessage(group, "Hi, <b>"+from_firstName+"</b>!\nWelcome in the "+bot.getChat(group)['title']+" group!", "HTML")

        groupUserCount = bot.getChatMembersCount(group)

        # Delete all commands
        if text.startswith("/"):
            bot.deleteMessage((group, msgId))

        # Admin message
        if isAdmin(from_id):
            if text.startswith("/warn @"):
                text_split = text.split(" ", 2)
                selectedUser = text_split[1]
                selectedUserData = db_users.search(where('username') == selectedUser.replace("@", ""))[0]['chatId']
                previousWarns = int(db_users.search(where('chatId') == selectedUserData)[0]['warns'])
                db_users.update({'warns': str(previousWarns + 1)}, where('chatId') == selectedUserData)
                userWarns = int(db_users.search(where('chatId') == selectedUserData)[0]['warns'])
                try:
                    reason = text_split[2]
                    bot.sendMessage(group, str("❗️️ " + selectedUser + " has been warned [" + str(userWarns) + "/3] for <b>" + reason + "</b>."), parse_mode="HTML")
                except IndexError:
                    bot.sendMessage(group, str("❗️️ " + selectedUser + " has been warned [" + str(userWarns) + "/3]."))
                if userWarns >= 3:
                    bot.kickChatMember(group, selectedUserData)
                    db_users.update({'warns': "0"}, where('chatId') == selectedUserData)
                    bot.sendMessage(group, str("🔇️ " + selectedUser + " has been banned."))

            elif text.startswith("/mute @"):
                text_split = text.split(" ", 2)
                selectedUser = text_split[1]
                selectedUserData = db_users.search(where('username') == selectedUser.replace("@", ""))[0]['chatId']
                bot.restrictChatMember(group, selectedUserData, until_date=time.time() + 3600)
                try:
                    reason = text_split[2]
                    bot.sendMessage(group, str("🔇️ " + selectedUser + " has been muted for <b>" + reason + "</b> until the next hour."), parse_mode="HTML")
                except IndexError:
                    bot.sendMessage(group, str("🔇️ " + selectedUser + " has been muted until the next hour."))

            elif text.startswith("/kick @"):
                text_split = text.split(" ", 2)
                selectedUser = text_split[1]
                selectedUserData = db_users.search(where('username') == selectedUser.replace("@", ""))[0]['chatId']
                bot.kickChatMember(group, selectedUserData)
                time.sleep(0.5)
                bot.unbanChatMember(group, selectedUserData)
                try:
                    reason = text_split[2]
                    bot.sendMessage(group, str("❗️️ "+selectedUser+" has been kicked for <b>"+reason+"</b>."), parse_mode="HTML")
                except IndexError:
                    bot.sendMessage(group, str("❗️️ "+selectedUser+" has been kicked."))

            elif text.startswith("/ban @"):
                text_split = text.split(" ", 2)
                selectedUser = text_split[1]
                selectedUserData = db_users.search(where('username') == selectedUser.replace("@", ""))[0]['chatId']
                bot.kickChatMember(group, selectedUserData)
                try:
                    reason = text_split[2]
                    bot.sendMessage(group, str("🚷 "+selectedUser+" has been banned for <b>"+reason+"</b>."), parse_mode="HTML")
                except IndexError:
                    bot.sendMessage(group, str("🚷 "+selectedUser+" has been banned."))

            elif text.startswith("/unban @"):
                text_split = text.split(" ", 1)
                selectedUser = text_split[1]
                selectedUserData = db_users.search(where('username') == selectedUser.replace("@", ""))[0]['chatId']
                bot.unbanChatMember(group, selectedUserData)
                bot.sendMessage(group, "✅️ "+str(selectedUser)+" unbanned.")

            elif text.startswith("/unwarn @"):
                text_split = text.split(" ", 1)
                selectedUser = text_split[1]
                selectedUserData = db_users.search(where('username') == selectedUser.replace("@", ""))[0]['chatId']
                previousWarns = int(db_users.search(where('chatId') == selectedUserData)[0]['warns'])
                if previousWarns > 0:
                    db_users.update({'warns': str(previousWarns-1)}, where('chatId') == selectedUserData)
                    bot.sendMessage(group, "❎ "+str(selectedUser)+" unwarned.\nHe now has "+str(previousWarns-1)+" warns.")

            elif text.startswith("/unmute @"):
                text_split = text.split(" ", 1)
                selectedUser = text_split[1]
                selectedUserData = db_users.search(where('username') == selectedUser.replace("@", ""))[0]['chatId']
                bot.restrictChatMember(group, selectedUserData, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
                bot.sendMessage(group, str("🔈 " + selectedUser + " unmuted."))

            elif text.startswith("/tell "):
                text_split = text.split(" ", 1)
                bot.sendMessage(group, text_split[1], parse_mode="HTML", reply_to_message_id=reply_msgId)

            elif text == "/reload":
                reloadAdmins()
                bot.sendMessage(group, "✅ <b>Bot reloaded!</b>", "HTML")

            elif text.startswith("/helper @"):
                text_split = text.split(" ", 2)
                selectedUser = text_split[1]
                selectedUserData = db_users.search(where('username') == selectedUser.replace("@", ""))[0]['chatId']
                if not isAdmin(selectedUserData):
                    updateAdminDatabase(selectedUserData, "helper")
                    bot.sendMessage(group, str("⛑ " + selectedUser + " is now <b>Helper</b>."), "HTML")

            elif text.startswith("/unhelper @"):
                text_split = text.split(" ", 2)
                selectedUser = text_split[1]
                selectedUserData = db_users.search(where('username') == selectedUser.replace("@", ""))[0]['chatId']
                if selectedUserData in [x["chatId"] for x in db_admins.search(where('status') == "helper")]:
                    db_admins.remove(where('chatId') == selectedUserData)
                    bot.sendMessage(group, str("⛑ " + selectedUser + " removed from <b>Helpers</b>."), "HTML")


            elif isReply:

                if text.startswith("/warn"):
                    previousWarns = int(db_users.search(where('chatId') == reply_fromId)[0]['warns'])
                    db_users.update({'warns': str(previousWarns + 1)}, where('chatId') == reply_fromId)
                    userWarns = int(db_users.search(where('chatId') == reply_fromId)[0]['warns'])
                    try:
                        reason = text.split(" ", 1)[1]
                        bot.sendMessage(group, str("❗️️ " + reply_firstName + " has been warned [" + str(userWarns) + "/3] for <b>" + reason + "</b>."), parse_mode="HTML", reply_to_message_id=reply_msgId)
                    except IndexError:
                        bot.sendMessage(group, str("❗️️ " + reply_firstName + " has been warned [" + str(userWarns) + "/3]."), reply_to_message_id=reply_msgId)
                    if userWarns >= 3:
                        bot.kickChatMember(group, reply_fromId)
                        db_users.update({'warns': "0"}, where('chatId') == reply_fromId)
                        bot.sendMessage(group, str("🔇️ " + reply_firstName + " has been banned."), reply_to_message_id=reply_msgId)

                elif text.startswith("/mute"):
                    bot.restrictChatMember(group, reply_fromId, until_date=time.time() + 3600)
                    try:
                        reason = text.split(" ", 1)[1]
                        bot.sendMessage(group, str("🔇️ " + reply_firstName + " has been muted for <b>" + reason + "</b> until the next hour."), parse_mode="HTML", reply_to_message_id=reply_msgId)
                    except IndexError:
                        bot.sendMessage(group, str("🔇️ " + reply_firstName + " has been muted until the next hour."), reply_to_message_id=reply_msgId)

                elif text.startswith("/kick"):
                    bot.kickChatMember(group, reply_fromId)
                    time.sleep(0.5)
                    bot.unbanChatMember(group, reply_fromId)
                    try:
                        reason = text.split(" ", 1)[1]
                        bot.sendMessage(group, str("❗️️ "+reply_firstName+" has been kicked for <b>"+reason+"</b>."), parse_mode="HTML", reply_to_message_id=reply_msgId)
                    except IndexError:
                        bot.sendMessage(group, str("❗️️ "+reply_firstName+" has been kicked."), reply_to_message_id=reply_msgId)

                elif text.startswith("/ban"):
                    bot.kickChatMember(group, reply_fromId)
                    try:
                        reason = text.split(" ", 1)[1]
                        bot.sendMessage(group, str("🚷 "+reply_firstName+" has been banned for <b>"+reason+"</b>."), parse_mode="HTML", reply_to_message_id=reply_msgId)
                    except IndexError:
                        bot.sendMessage(group, str("🚷 "+reply_firstName+" has been banned."), reply_to_message_id=reply_msgId)

                elif text.startswith("/unban"):
                    bot.unbanChatMember(group, reply_fromId)
                    bot.sendMessage(group, "✅️ "+str(reply_firstName)+" unbanned.", reply_to_message_id=reply_msgId)

                elif text.startswith("/unwarn"):
                    previousWarns = int(db_users.search(where('chatId') == reply_fromId)[0]['warns'])
                    if previousWarns > 0:
                        db_users.update({'warns': str(previousWarns-1)}, where('chatId') == reply_fromId)
                        bot.sendMessage(group, "❎ "+reply_firstName+" unwarned.\nHe now has "+str(previousWarns-1)+" warns.", reply_to_message_id=reply_msgId)

                elif text.startswith("/unmute"):
                    bot.restrictChatMember(group, reply_fromId, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
                    bot.sendMessage(group, str("🔈 " + reply_firstName + " unmuted."), reply_to_message_id=reply_msgId)

                elif text.startswith("/helper"):
                    if not isAdmin(reply_fromId):
                        updateAdminDatabase(reply_fromId, "helper")
                        bot.sendMessage(group, str("⛑ " + reply_firstName + " is now <b>Helper</b>."), parse_mode="HTML", reply_to_message_id=reply_msgId)

                elif text.startswith("/unhelper"):
                    if reply_fromId in [x["chatId"] for x in db_admins.search(where('status') == "helper")]:
                        db_admins.remove(where('chatId') == reply_fromId)
                        bot.sendMessage(group, str("⛑ " + reply_firstName + " removed from <b>Helpers</b>."), parse_mode="HTML", reply_to_message_id=reply_msgId)


        # Normal user message
        cmdtext = text.replace(myusername, "")
        if cmdtext == "/staff":
            message = "🔰️ <b>GROUP STAFF</b> 🔰️"

            message += "\n\n  ⚜️ <b>Founder</b>"
            for x in [x["chatId"] for x in db_admins.search(where('status') == "creator")]:
                try:
                    message += "\n        @" + bot.getChatMember(group, x)['user']['username']
                except KeyError:
                    message += "\n        " + bot.getChatMember(group, x)['user']['first_name']

            message += "\n\n  👮🏻‍♀ <b>Admins</b>"
            for x in [x["chatId"] for x in db_admins.search(where('status') == "admin")]:
                try:
                    message += "\n        @" + bot.getChatMember(group, x)['user']['username']
                except KeyError:
                    message += "\n        " + bot.getChatMember(group, x)['user']['first_name']

            message += "\n\n  ⛑ <b>Helpers</b>"
            for x in [x["chatId"] for x in db_admins.search(where('status') == "helper")]:
                try:
                    message += "\n        @" + bot.getChatMember(group, x)['user']['username']
                except KeyError:
                    message += "\n        " + bot.getChatMember(group, x)['user']['first_name']
            bot.sendMessage(group, message, parse_mode="HTML")


bot, group, groupUserCount, myusername = initialize()
reloadAdmins()
bot.message_loop({'chat': handle})
while True:
    time.sleep(60)