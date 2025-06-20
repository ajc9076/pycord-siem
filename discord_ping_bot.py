"""
Discord Bot that pings the periodic gaming server to check if it has internet connectivity.

Author: hibobjr

Date: 12/24/2022
"""

# std imports
from os import getenv, path
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM
from typing import Any, Callable
from subprocess import call, DEVNULL
from time import sleep
from platform import system
from functools import partial
from json import load, dumps
from threading import Lock
# 3rd party imports
from dotenv import load_dotenv
from discord_webhook import DiscordWebhook
from discord import app_commands, TextChannel, Client, Intents, Object, Interaction


# set up the discord bot
intents = Intents.default()
intents.message_content = True
botClient = Client(intents=intents)
tree = app_commands.CommandTree(botClient)
# load secrets
load_dotenv()
token = getenv('DISCORD_TOKEN')
webhook = getenv('WEBHOOK_URL')
host = getenv('HOST_TO_CHECK')
guild_id = int(getenv('DISCORD_GUILD_ID'))


class PingStatus:
    """
    Create a class that stores the statuses of various ping checks.

    Using an object to store this means it updates globally.
    """
    def __init__(self) -> None:
        self.ping_status_locker = Lock()
        # read config file if it exists
        if path.exists("/home/hibobjr/monitor/checks.json"):
            with open("/home/hibobjr/monitor/checks.json", 'r', encoding='utf8') as checks:
                self.ping_servers = load(checks)
        else:
            self.ping_servers = {"ping_server": True, "ping_rub": True, "ping_dub": False, "ping_os": False, "ping_ssh": False}
            with open("/home/hibobjr/monitor/checks.json", 'w', encoding='utf8') as checks:
                checks.write(dumps(self.ping_servers))

    def toggle_ping_server(self) -> None:
        """
        Toggles whether the bot does any checks at all

        :return: None
        """
        with self.ping_status_locker:
            # toggle the status
            if self.ping_servers["ping_server"]:
                self.ping_servers["ping_server"] = False
            else:
                self.ping_servers["ping_server"] = True
            # write to file to persist
            with open("/home/hibobjr/monitor/checks.json", 'w', encoding='utf8') as checks:
                checks.write(dumps(self.ping_servers))

    def toggle_ping_rub(self) -> None:
        """
        Toggles the status for pinging the Rubidium server

        :return: None
        """
        with self.ping_status_locker:
            # toggle the status
            if self.ping_servers["ping_rub"]:
                self.ping_servers["ping_rub"] = False
            else:
                self.ping_servers["ping_rub"] = True
            # write to file to persist
            with open("/home/hibobjr/monitor/checks.json", 'w', encoding='utf8') as checks:
                checks.write(dumps(self.ping_servers))

    def toggle_ping_dub(self) -> None:
        """
        Toggles the status for pinging the Dubnium server

        :return: None
        """
        with self.ping_status_locker:
            # toggle the status
            if self.ping_servers["ping_dub"]:
                self.ping_servers["ping_dub"] = False
            else:
                self.ping_servers["ping_dub"] = True
            # write to file to persist
            with open("/home/hibobjr/monitor/checks.json", 'w', encoding='utf8') as checks:
                checks.write(dumps(self.ping_servers))

    def toggle_ping_os(self) -> None:
        """
        Toggles the status for pinging the Osmium server

        :return: None
        """
        with self.ping_status_locker:
            # toggle the status
            if self.ping_servers["ping_os"]:
                self.ping_servers["ping_os"] = False
            else:
                self.ping_servers["ping_os"] = True
            # write to file to persist
            with open("/home/hibobjr/monitor/checks.json", 'w', encoding='utf8') as checks:
                checks.write(dumps(self.ping_servers))

    def toggle_ping_ssh(self) -> None:
        """
        Toggles the status for pinging the SSH server

        :return: None
        """
        with self.ping_status_locker:
            # toggle the status
            if self.ping_servers["ping_ssh"]:
                self.ping_servers["ping_ssh"] = False
            else:
                self.ping_servers["ping_ssh"] = True
            # write to file to persist
            with open("/home/hibobjr/monitor/checks.json", 'w', encoding='utf8') as checks:
                checks.write(dumps(self.ping_servers))


def get_channels() -> list[TextChannel]:
    """
    Gets a list of text channels the bot is in.

    Use .id on each TextChannel to get the id

    :return: <list> TextChannel objects
    """
    text_channel_list = []
    for server in botClient.guilds:
        for channel in server.text_channels:
            text_channel_list.append(channel)
    return text_channel_list


def ping_server() -> bool:
    """
    Ping the host once to check connectivity.

    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.

    :return: True if host (str) responds to a ping request.
    """
    # Option for the number of packets as a function of
    param = '-n' if system().lower() == 'windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    return call(command, stdout=DEVNULL) == 0


def tcp_connect(port: int) -> bool:
    """
    Check if you can connect to a specific port on the host.

    A successful connection indicates a service is running on the port,
    but does not tell you what service it is (this is assumed based on port number).

    :return: <bool> True if the connection was successful.
    """
    s = socket(AF_INET, SOCK_STREAM)
    s.settimeout(2)
    result = s.connect_ex((host, port))
    s.close()
    if result == 0:
        return True
    else:
        return False


def ping_osmium() -> bool:
    """
    Use UDP to ping the Osmium (Unturned server) port 27015

    :return: <bool> True if the server is up, False if not
    """
    # the message to send to the server
    message = b"\xff\xff\xff\xff\x54\x53\x6f\x75\x72\x63\x65\x20\x45\x6e\x67\x69\x6e\x65\x20\x51\x75\x65\x72\x79\x00"
    # set up the UDP connection
    s = socket(AF_INET, SOCK_DGRAM)
    s.settimeout(2)
    # attempt to send the message
    try:
        s.sendto(message, (host, 27015))
        s.recv(1024)
        # if data was received successfully, then we have a connection
        return True
    except:
        return False


@botClient.event
async def on_ready() -> None:
    """
    When the bot successfully boots up, print a message to the channel and start server pings

    :return: None
    """
    await tree.sync(guild=Object(id=guild_id))
    print(f'{botClient.user.name} has connected to Discord!')
    # get a list of channels that have been connected to
    text_channel_list = get_channels()
    channel = botClient.get_channel(text_channel_list[0].id)
    await channel.send("Bot is Online! Beginning server checks...")
    await run_blocking(start_monitoring)


def start_monitoring() -> None:
    """
    Function that checks server statuses.

    Uses webhooks to bypass the need for async/await

    :return: None
    """
    while status.ping_servers["ping_server"]:
        if ping_server():
            result = f""
            if status.ping_servers["ping_rub"]:
                if not tcp_connect(25565):
                    result += f"Rubidium ({host}:25565) is down!\n"
            if status.ping_servers["ping_dub"]:
                if not tcp_connect(25566):
                    result += f"Dubnium ({host}:25566) is down!\n"
            if status.ping_servers["ping_os"]:
                if not ping_osmium():
                    result += f"Osmium ({host}:27015) is down!\n"
            if status.ping_servers["ping_ssh"]:
                if not tcp_connect(22):
                    result += f"SSH ({host}:22) is down!\n"

            if result != f"":
                DiscordWebhook(url=webhook, content=result).execute()
        else:
            DiscordWebhook(url=webhook, content=f"{host} is down!").execute()
        sleep(60)


async def run_blocking(blocking_func: Callable, *args, **kwargs) -> Any:
    """
    Basically create a new thread to run the specified function.

    Note: the function cannot be an async/await function.

    :param blocking_func: The function to be called in the new thread

    :param args: the args passed to the function

    :param kwargs: the kwargs passed to the function

    :return: Any output from the spawned function
    """
    func = partial(blocking_func, *args, **kwargs)
    return await botClient.loop.run_in_executor(None, func)


@tree.command(name='toggle', 
              description='Enabled or disables checking a server from [rubidium, dubnium, osmium, ssh]', 
              guild=Object(id=guild_id))
async def disable_ping(ctx: Interaction, server_to_check: str) -> None:
    """
    A bot command that toggles on or off specific server pings to prevent spam when a server is purposely offline

    :param ctx: The context which the command was sent (which channel, when, etc.)

    :param check_to_stop: The name of the server to start/stop checking

    :return: None
    """
    match server_to_check.lower():
        case "all":
            if status.ping_servers["ping_server"]:
                await ctx.response.send_message("Stopping server checks...")
            else:
                await ctx.response.send_message("Beginning server checks...")
            status.toggle_ping_server()
        case "rubidium":
            status.toggle_ping_rub()
            await ctx.response.send_message("Checking Rubidium connectivity: " + str(status.ping_servers["ping_rub"]))
        case "dubnium":
            status.toggle_ping_dub()
            await ctx.response.send_message("Checking Dubnium connectivity: " + str(status.ping_servers["ping_dub"]))
        case "osmium":
            status.toggle_ping_os()
            await ctx.response.send_message("Checking Osmium connectivity: " + str(status.ping_servers["ping_os"]))
        case "ssh":
            status.toggle_ping_ssh()
            await ctx.response.send_message("Checking SSH connectivity: " + str(status.ping_servers["ping_ssh"]))
        case _:
            await ctx.response.send_message("Unknown parameter. Please use 'all', 'rubidium', 'dubnium', 'osmium', or 'ssh'")


@tree.command(name='status', 
              description='Lists current status of everything on the server', 
              guild=Object(id=guild_id))
async def get_status(ctx: Interaction) -> None:
    """
    Lists current status of everything on the server

    :param ctx: The context which the command was sent (which channel, when, etc.)

    :return: None
    """
    send_block = f"```\n"

    send_block += f"RUNNING CHECKS: {status.ping_servers["ping_server"]}\n"
    send_block += f"RUBIDIUM CHECKS: {status.ping_servers["ping_rub"]}\n"
    send_block += f"DUBNIUM CHECKS: {status.ping_servers["ping_dub"]}\n"
    send_block += f"OSMIUM CHECKS: {status.ping_servers["ping_os"]}\n"
    send_block += f"SSH CHECKS: {status.ping_servers["ping_ssh"]}\n"

    send_block += f"```"
    await ctx.response.send_message(send_block)

# create the global object to store ping statuses
status = PingStatus()
