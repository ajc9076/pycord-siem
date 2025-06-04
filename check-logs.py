"""
Script to send data about the server back to the Discord Web Hook.

Essentially a discord-based SIEM

Author: hibobjr

Date: 12/24/2022
"""

# std imports
from threading import Thread, main_thread
from os import path, getenv
from time import sleep
# 3rd party imports
from lz.reversal import reverse
from discord_webhook import DiscordWebhook
from dotenv import load_dotenv
# local imports
from discord_ping_bot import botClient, token


# set up secrets
load_dotenv()
WEBHOOK = getenv('WEBHOOK_URL')
# set up static text
SSH_TEXT = "New SSH Login detected! Content:\n"
RESTART_TEXT = "Service Restarted! Potential server restart occured..."
IP_CHANGED_TEXT = "DUC: IP Changed! Current IP: `"


def check_ssh_logs() -> None:
    """
    Read auth.log and check if any successful logins occurred

    :return: None
    """
    with open("/home/hibobjr/monitor/Known-login.txt", 'r') as login:
        known_login = login.readline()
    while main_thread().is_alive():
        with open('/var/log/auth.log', 'r') as auth_log:
            for line in reverse(auth_log):
                if "sshd" in line and "Accepted " in line:
                    if known_login != line:
                        with open("/home/hibobjr/monitor/Known-login.txt", 'w') as login:
                            login.write(line)
                        known_login = line
                        DiscordWebhook(url=WEBHOOK, content=SSH_TEXT+known_login).execute()
                        break
                    else:
                        break
        sleep(60)


def check_ip() -> None:
    """
    Report if the IP address has changed.

    Requires that a file /tmp/ip_changed has the IP in it.

    Theoretically you could run noip-duc so that it outputs the new IP to this file.
    
    :return: None
    """
    if path.exists("/tmp/ip_changed"):
        with open("/tmp/ip_changed", 'r', encoding='utf8') as ipfile:
            old_ip = ipfile.readline()
    else:
        old_ip = "0.0.0.0"

    while main_thread().is_alive():
        if path.exists("/tmp/ip_changed"):
            with open("/tmp/ip_changed", 'r', encoding='utf8') as ipfile:
                ip = ipfile.readline()
            if ip != old_ip:
                DiscordWebhook(url=WEBHOOK, content=IP_CHANGED_TEXT+ip+"`").execute()
                old_ip = ip

        sleep(60)


def main() -> None:
    """
    Main function to spawn all the monitor threads.

    Joins all the threads so this function never exits.

    :return: None
    """
    # Notify via discord that the service was restarted (most likely due to server restart)
    DiscordWebhook(url=WEBHOOK, content=RESTART_TEXT).execute()

    threads = []
    # spawn thread to watch ssh logs
    ssh_checker = Thread(target=check_ssh_logs)
    ssh_checker.start()
    threads.append(ssh_checker)
    # spawn thread to watch Rubidium errors
    # TODO

    # spawn thread to watch Dubnium errors
    # TODO

    # spawn thread to watch for IP changes
    ip_checker = Thread(target=check_ip)
    ip_checker.start()
    threads.append(ip_checker)

    # start the discord bot
    botClient.run(token)

    # join the threads (to prevent the program from terminating)
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    main()
