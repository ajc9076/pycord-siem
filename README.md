# pycord-siem

Basically run a siem through discord.

Monitor logs, system information, and service connectivity through discord. Even allows partial configuration using discord

## Requirements

1. Install requirements from requirements.txt
2. Setup an .env file with...
  - DISCORD_TOKEN (your application token from Discord)
  - WEBHOOK_URL (a webhook URL linked to your Discord server)
  - DISCORD_GUILD_ID (the ID to the same Discord server your webhook is in)
  - HOST_TO_CHECK (hostname of your server that you are checking)
3. Setup NoIP-DUC to save the IP changed file to `/tmp/ip_changed`
4. Run the script using a service for persistence