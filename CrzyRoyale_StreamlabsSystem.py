"""
Programmer: TheCrzyDoctor
Description: This script enables you to have a battle royale in your chat.
Date: 02/19/2018
Version: 1
"""

# ---------------------------------------
# Import Libraries
# ---------------------------------------

import clr
import os
import codecs
import json
import random
import datetime
import sys

clr.AddReference("IronPython.SQLite.dll")
clr.AddReference("IronPython.Modules.dll")

sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))
import CRConfigs

# ---------------------------------------
# [Required] Script Information
# ---------------------------------------
ScriptName = "Crzy Royale"
Website = "https://www.twitch.tv/thecrzydoc"
Description = "This script enables you to have a battle royale in your chat."
Creator = "TheCrzyDoctor"
Version = "1.0.5"

# ---------------------------------------
# Settings file setup
# ---------------------------------------

settingsFile = os.path.join(os.path.dirname(__file__), "settings.json")
DatabaseFile = os.path.join(os.path.dirname(__file__), "CRRoyale.sqlite")
# global vars that dont need to be saved
users_in_cr = {}


class Settings:
    def __init__(self, settingsFile=None):
        if settingsFile is not None and os.path.isfile(settingsFile):
            with codecs.open(settingsFile, encoding='utf-8-sig', mode='r') as f:
                self.__dict__ = json.load(f, encoding='utf-8-sig')
        else:
            self.OnlyLive = False
            self.Command = '!crstart'
            self.cmdJoin = '!crjoin'
            self.cmdLoot = '!crloot'
            self.cmdAttack = '!crattack'
            self.cmdListofAttackers = "!crlist"
            self.Usage = 'Stream Chat'
            self.Permission = 'Everyone'
            self.CrzyRoyaleCost = 10
            self.PermissionInfo = ''
            self.PermissionResp = '{0} -> only {1} and higher can use this command'
            self.CRCreatedMsg = 'The Crzy Royale has been started. Use !crjoin to join the Crzy Royale'
            self.CRErrorMsg = 'There was an issue with creating the Crzy Royale'
            self.JoinedCrzyRoyale = '{0} joined the Crzy Royale.'
            self.AlreadyJoined = '{0}, you are already in the Crzy Royale.'
            self.LootWon = '{0} just obtained level {1} loot.'
            self.AlreadyLoot = '{0} you can only loot once.'
            self.AttackOver = '{0} has killed {1}'
            self.CrzyRoyaleWon = '{0} has won the Crazy Royale'
            self.CRLoser = 10
            self.CRWinner = 50
            self.UseCD = True
            self.CoolDown = 1000
            self.OnCoolDown = "{0} the command is still on cooldown for {1} seconds!"
            self.UserCoolDown = 10
            self.OnUserCoolDown = "{0} the command is still on user cooldown for {1} seconds!"
            self.CasterCD = True
            self.NoCurrency = "{0} -> You don't have any currency to participate in the crzy royale!"
            self.InfoResponse = 'Info coming in next version'

    def ReloadSettings(self, data):
        """ Reload settings file. """
        self.__dict__ = json.loads(data, encoding='utf-8-sig')
        return

    def SaveSettings(self, settingsFile):
        """ Saves settings File """
        with codecs.open(settingsFile, encoding='utf-8-sig', mode='w+') as f:
            json.dump(self.__dict__, f, encoding='utf-8-sig')
        with codecs.open(settingsFile.replace("json", "js"), encoding='utf-8-sig', mode='w+') as f:
            f.write("var settings = {0};".format(json.dumps(self.__dict__, encoding='utf-8-sig')))


def ReloadSettings(jsonData):
    """ Reload Settings on Save """
    global CRSettings
    CRSettings.ReloadSettings(jsonData)
    return


# ---------------------------------------
# 	[Required] Functions
# ---------------------------------------
def Init():
    """ Intialize Data (only called on load) """
    global CRSettings
    CRSettings = Settings(settingsFile)
    return


def Execute(data):
    """ Executes data and processes the message. """

    if data.IsChatMessage():
        # check what command is being used.

        # make sure the user has enough points
        if Parent.GetPoints(data.User) < CRSettings.CrzyRoyaleCost:
            message = CRSettings.NoCurrency.format(data.UserName)
            SendResp(data, CRSettings.Usage, message)
            return

        if data.GetParam(0).lower() == CRSettings.Command.lower() and not CRConfigs.started:
            CRConfigs.started = True
            CRConfigs.allowJoin = True
            CRConfigs.allowLoot = True
            SendResp(data, CRSettings.Usage, CRSettings.CRCreatedMsg)
        elif data.GetParam(0).lower() == CRSettings.cmdJoin.lower() and CRConfigs.allowJoin is True:
            # set default value for loot when they join
            if data.User not in CRConfigs.participants:
                CRConfigs.participants[data.User] = 0
                SendResp(data, CRSettings.Usage, CRSettings.JoinedCrzyRoyale.format(data.User))
                Parent.RemovePoints(data.User, CRSettings.CrzyRoyaleCost)
                if len(CRConfigs.participants) >= 2:
                    CRConfigs.allowAttack = True
            else:
                SendResp(data, CRSettings.Usage, CRSettings.AlreadyJoined.format(data.User))
        elif data.GetParam(0).lower() == CRSettings.cmdLoot.lower() and CRConfigs.allowLoot is True:
            if data.User not in CRConfigs.hasLooted:
                r = random.randint(0, 6)
                CRConfigs.participants[data.User] = r
                SendResp(data, CRSettings.Usage, CRSettings.LootWon.format(data.User, r))
                CRConfigs.hasLooted.append(data.User)
            else:
                SendResp(data, CRSettings.Usage, CRSettings.AlreadyLoot.format(data.User))
        elif data.GetParam(0).lower() == CRSettings.cmdAttack.lower() and data.GetParamCount() == 2 and CRConfigs.allowAttack is True:
            if CRConfigs.participants[data.User] > CRConfigs.participants[data.GetParam(1)]:
                SendResp(data, CRSettings.Usage, CRSettings.AttackOver.format(data.User, data.GetParam(1)))
                del CRConfigs.participants[data.GetParam(1)]
                if len(CRConfigs.participants) == 1:
                    # Announce the winner
                    SendResp(data, CRSettings.Usage,
                             CRSettings.CrzyRoyaleWon.format(next(iter(CRConfigs.participants))))
                    # Add predefined amount of points
                    Parent.AddPoints(data.User, CRSettings.CRWinner)
                    CRConfigs.started = False
                    CRConfigs.allowJoin = False
                    CRConfigs.allowLoot = False
                    CRConfigs.allowAttack = False
                    del CRConfigs.hasLooted[:]
                    CRConfigs.participants.clear()
                return
            else:
                SendResp(data, CRSettings.Usage, CRSettings.AttackOver.format(data.GetParam(1), data.User))
                del CRConfigs.participants[data.User]
                if len(CRConfigs.participants) == 1:
                    # Announce the winner
                    SendResp(data, CRSettings.Usage,
                             CRSettings.CrzyRoyaleWon.format(next(iter(CRConfigs.participants))))
                    # Add predefined amount of points
                    Parent.AddPoints(data.User, CRSettings.CRWinner)
                    CRConfigs.started = False
                    CRConfigs.allowJoin = False
                    CRConfigs.allowLoot = False
                    CRConfigs.allowAttack = False
                    del CRConfigs.hasLooted[:]
                    CRConfigs.participants.clear()
                return
        elif data.GetParam(0).lower() == CRSettings.cmdListofAttackers and CRConfigs.started:
            players = ''
            for k in CRConfigs.participants:
                players = players + "{0},".format(k)

            msg = "Players Currently in Crzy Royale - {0}".format(players)
            SendResp(data, CRSettings.Usage, msg)
        elif not CRConfigs.started and data.GetParam(0).lower() == CRSettings.Command.lower() \
                or data.GetParam(0).lower() == CRSettings.cmdAttack.lower() \
                or data.GetParam(0).lower() == CRSettings.cmdLoot.lower() \
                or data.GetParam(0).lower() == CRSettings.Command.lower():
            SendResp(data, CRSettings.Usage, 'Crzy Royale has not started yet. Please wait till someone starts it.')
            return

        return


def Tick():
    """Required tick function"""
    pass


# ---------------------------------------
# 	[Optional] Usage functions
# ---------------------------------------

def SendResp(data, rUsage, sendMessage):
    """Sends message to Stream or discord chat depending on settings"""

    # Set a list with all possible usage options that would trigger Stream chat message
    l = ["Stream Chat", "Chat Both", "All", "Stream Both"]

    # check if message is from Stream, from chat and if chosen usage is in the list above
    if (data.IsFromTwitch() or data.IsFromYoutube()) and (rUsage in l) and not data.IsWhisper():
        # send Stream message
        Parent.SendStreamMessage(sendMessage)

    # Set a list with all possible usage options that would trigger Stream whisper
    l = ["Stream Whisper", "Whisper Both", "All", "Stream Both"]

    # check if message is from Stream, from whisper and if chosen usage is in the list above
    if (data.IsFromTwitch() or data.IsFromYoutube()) and data.IsWhisper() and (rUsage in l):
        # send Stream whisper
        Parent.SendStreamWhisper(data.User, sendMessage)

    # Set a list with all possible usage options that would trigger discord message
    l = ["Discord Chat", "Chat Both", "All", "Discord Both"]

    # check if message is from discord
    if data.IsFromDiscord() and not data.IsWhisper() and (rUsage in l):
        # send Discord message
        Parent.SendDiscordMessage(sendMessage)

    # Set a list with all possible usage options that would trigger discord DM
    l = ["Discord Whisper", "Whisper Both", "All", "Discord Both"]

    # check if message is from discord, from DM and if chosen usage is in the list above
    if data.IsFromDiscord() and data.IsWhisper() and (rUsage in l):
        # send Discord whisper
        Parent.SendDiscordDM(data.User, sendMessage)

    return


"""
Required custom fucntions needed for plugin.
"""


def OpenReadMe():
    """Open the readme.txt in the scripts folder"""
    location = os.path.join(os.path.dirname(__file__), "README.txt")
    os.startfile(location)
    return


def haspermission(data):
    """ CHecks to see if the user hs the correct permission.  Based on Castorr91's Gamble"""
    if not Parent.HasPermission(data.User, CRSettings.Permission, CRSettings.PermissionInfo):
        message = CRSettings.PermissionResp.format(data.UserName, CRSettings.Permission, CRSettings.PermissionInfo)
        SendResp(data, CRSettings.Usage, message)
        return False
    return True


def is_on_cooldown(data):
    """ Checks to see if user is on cooldown. Based on Castorr91's Gamble"""
    # check if command is on cooldown
    cooldown = Parent.IsOnCooldown(ScriptName, CRSettings.Command)
    user_cool_down = Parent.IsOnUserCooldown(ScriptName, CRSettings.Command, data.User)
    caster = Parent.HasPermission(data.User, "Caster", "")

    if (cooldown or user_cool_down) and caster is False and not CRSettings.CasterCD:

        if CRSettings.UseCD:
            cooldownDuration = Parent.GetCooldownDuration(ScriptName, CRSettings.Command)
            userCDD = Parent.GetUserCooldownDuration(ScriptName, CRSettings.Command, data.User)

            if cooldownDuration > userCDD:
                m_CooldownRemaining = cooldownDuration

                message = CRSettings.OnCoolDown.format(data.UserName, m_CooldownRemaining)
                SendResp(data, CRSettings.Usage, message)

            else:
                m_CooldownRemaining = userCDD

                message = CRSettings.OnUserCoolDown.format(data.UserName, m_CooldownRemaining)
                SendResp(data, CRSettings.Usage, message)
        return True
    elif (cooldown or user_cool_down) and CRSettings.CasterCD:
        if CRSettings.UseCD:
            cooldownDuration = Parent.GetCooldownDuration(ScriptName, CRSettings.Command)
            userCDD = Parent.GetUserCooldownDuration(ScriptName, CRSettings.Command, data.User)

            if cooldownDuration > userCDD:
                m_CooldownRemaining = cooldownDuration

                message = CRSettings.OnCoolDown.format(data.UserName, m_CooldownRemaining)
                SendResp(data, CRSettings.Usage, message)

            else:
                m_CooldownRemaining = userCDD

                message = CRSettings.OnUserCoolDown.format(data.UserName, m_CooldownRemaining)
                SendResp(data, CRSettings.Usage, message)
        return True
    return False


def addcooldown(data):
    """Create Cooldowns Based on Castorr91's Gamble"""
    if Parent.HasPermission(data.User, "Caster", "") and CRSettings.CasterCD:
        Parent.AddCooldown(ScriptName, CRSettings.Command, CRSettings.CoolDown)
        return

    else:
        Parent.AddUserCooldown(ScriptName, CRSettings.Command, data.User, CRSettings.UserCoolDown)
        Parent.AddCooldown(ScriptName, CRSettings.Command, CRSettings.CoolDown)
