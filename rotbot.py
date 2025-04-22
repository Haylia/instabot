import discord
import os
import requests
import instaloader
import sys
import json
import traceback
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('DISCORD_PREFIX')

from discord.ext import commands, tasks
from discord import guild, embeds, Embed, InteractionResponse
from discord.utils import get

intents = discord.Intents.all()
bot_activity = discord.Game(name = "reel after reel after reel")

help_command = commands.DefaultHelpCommand(
    no_category = 'Commands'
)

client = commands.Bot(command_prefix = PREFIX, intents = intents, case_insensitive = True, activity = bot_activity, help_command=help_command)
timenow = datetime.now()

userwithunreaddms = []

instaloaderL = instaloader.Instaloader()

def get_real_instagram_url(share_url):
    try:
        response = requests.get(share_url, allow_redirects=True)
        return response.url  # This is the real post URL
    except Exception as e:
        print(f"Error fetching real Instagram URL: {e}")
        return None

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        if type(error) == discord.ext.commands.errors.MemberNotFound:
            await ctx.send("I could not find that member, check the spelling!")    
        else:
            await ctx.send("You made an error in the command arguments")
        print(type(error), error)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You are missing a piece of this command!")
        print(error)
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send("Command failed to run")
        #print out the line number that the error happened on
        # error with traceback is error.with_traceback
        print(error)
        traceback.print_exception(type(error), error, error.__traceback__)
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        await ctx.send("there's an error in this command")
        raise error
    
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith(PREFIX):
        print(f"Command: {message.content} sent by {message.author.name} in {message.guild.name}")
        await client.process_commands(message)


@client.command()
async def ping(ctx):
    await ctx.send(f'{round(client.latency * 1000)}ms')

# this bot expects links from instagram that are reels or posts. its job is to download them and resend them to the ctx channel and delete them after

@client.command()
async def dmhaul(ctx, user: discord.User=None):
    if user is None:
        # the user is the ctx.author
        user = ctx.author
    if user.dm_channel is None:
        await user.create_dm()
        # await user.dm_channel.send(f"Hello {user.name}, there's been a meme haul request but you've not sent me anything. RIP")
    
    # try to get the message history
    # iterate through messages since the last bot message in the channel, newest first
    # await ctx.send(f"Getting terrible instagram memes from {user.display_name}'s dms")
    sentany = False
    async with ctx.typing():
        async for message in user.dm_channel.history(oldest_first=False):
            if message.author == client.user:
                # this is the bot message, break
                break
            else:
                # expecting instagram link, if not, skip
                # check if the message is a link
                if message.content.startswith("https://www.instagram.com/") or message.content.startswith("https://instagram.com/"):
                    reallink = get_real_instagram_url(message.content)
                    # check if the link is a reel or post
                    if "/p/" in reallink:
                        # get the link
                        link = reallink
                        # get the id of the post/
                        try:
                            post = instaloader.Post.from_shortcode(instaloaderL.context, link.split("/")[-2])
                            # download the post
                            diddownload = instaloaderL.download_pic(filename=post.shortcode, url=post.url, mtime=post.date_utc)
                            if diddownload:
                                # send the file to the ctx channel
                                await ctx.send(file=discord.File(f"{post.shortcode}.jpg"))
                                # delete the file
                                os.remove(f"{post.shortcode}.jpg")
                                sentany = True
                        except Exception as e:
                            print(e)
                    elif "/reel/" in reallink:
                        try:
                            # get the link
                            link = reallink
                            # get the id of the reel
                            post = instaloader.Post.from_shortcode(instaloaderL.context, link.split("/")[-2])
                            video_url = post.video_url
                            filename = instaloaderL.format_filename(post, target=post.owner_username)
                            diddownload = instaloaderL.download_pic(filename=filename, url=video_url, mtime=post.date_utc)
                            if diddownload:
                                filename = filename + ".mp4"
                                # send the file to the ctx channel
                                await ctx.send(file=discord.File(filename))
                                # delete the file
                                os.remove(filename)
                                sentany = True
                        except Exception as e:
                            print(e)
                    else:
                        # this is not a reel or post, skip
                        continue
                    
        # send a message in the user's dm channel (will be used to mark messages that have already been scanned)
        if sentany:
            await user.dm_channel.send(f"Sent to here")

@client.command()
async def dmcheck(ctx):
    global userwithunreaddms
    # check all users in guild for new dms since the last bot message, output the count per member
    memberstomessages = dict()
    # get all members in the guild
    # iterate through all members
    async with ctx.typing():
        for user in client.users:
            try:
                messages = 0
                if user == client.user:
                    # skip the bot
                    print("skipping self")
                    continue
                if not user.dm_channel:
                    await user.create_dm()
                    memberstomessages[user] = messages
                # check if the user has sent any messages since the last bot message
                async for message in user.dm_channel.history(oldest_first=False):
                    if message.author == client.user:
                        # this is the bot message, break
                        break
                    else:
                        # this is not the bot message, increment the count
                        messages += 1
                memberstomessages[user] = messages
                print(f"{user.display_name} has {messages} messages since the last bot message")
            except:
                # this user can't be dmed
                continue
        # sort the dictionary by value
        memberstomessages = dict(sorted(memberstomessages.items(), key=lambda item: item[1], reverse=True))
        # create an embed
        embed = Embed(title="DM Check", description="", color=discord.Color.blue())
        # iterate through the dictionary and add fields to the embed
        for user, messages in memberstomessages.items():
            if messages > 0:
                embed.add_field(name=user.display_name, value=messages, inline=False)
                userwithunreaddms.append(user.id)
        # send the embed to the ctx channel
        await ctx.send(embed=embed)
    
@client.command()
async def dmhaulall(ctx):
    global userwithunreaddms
    for userid in userwithunreaddms:
        user = client.get_user(userid)
        
        # if user.dm_channel is None:
        #     await user.create_dm()
            # await user.dm_channel.send(f"Hello {user.name}, there's been a meme haul request but you've not sent me anything. RIP")

        # try to get the message history
        # iterate through messages since the last bot message in the channel, newest first
        await ctx.send("From: " + user.display_name)
        sentany = False
        async with ctx.typing():
            async for message in user.dm_channel.history(oldest_first=False):
                if message.author == client.user:
                    # this is the bot message, break
                    break
                else:
                    # expecting instagram link, if not, skip
                    # check if the message is a link
                    if message.content.startswith("https://www.instagram.com/") or message.content.startswith("https://instagram.com/"):
                        reallink = get_real_instagram_url(message.content)
                        # check if the link is a reel or post
                        if "/p/" in reallink:
                            # get the link
                            link = reallink
                            # get the id of the post/
                            try:
                                post = instaloader.Post.from_shortcode(instaloaderL.context, link.split("/")[-2])
                                # download the post
                                diddownload = instaloaderL.download_pic(filename=post.shortcode, url=post.url, mtime=post.date_utc)
                                if diddownload:
                                    # send the file to the ctx channel
                                    await ctx.send(file=discord.File(f"{post.shortcode}.jpg"))
                                    # delete the file
                                    os.remove(f"{post.shortcode}.jpg")
                                    sentany = True
                            except Exception as e:
                                print(e)
                        elif "/reel/" in reallink:
                            try:
                                # get the link
                                link = reallink
                                # get the id of the reel
                                post = instaloader.Post.from_shortcode(instaloaderL.context, link.split("/")[-2])
                                video_url = post.video_url
                                filename = instaloaderL.format_filename(post, target=post.owner_username)
                                diddownload = instaloaderL.download_pic(filename=filename, url=video_url, mtime=post.date_utc)
                                if diddownload:
                                    filename = filename + ".mp4"
                                    # send the file to the ctx channel
                                    await ctx.send(file=discord.File(filename))
                                    # delete the file
                                    os.remove(filename)
                                    sentany = True
                            except Exception as e:
                                print(e)
                        else:
                            # this is not a reel or post, skip
                            continue
                        
            # send a message in the user's dm channel (will be used to mark messages that have already been scanned)
            if sentany or userid in userwithunreaddms:
                await user.dm_channel.send(f"Sent to here")
                userwithunreaddms.remove(userid)


client.run(TOKEN)