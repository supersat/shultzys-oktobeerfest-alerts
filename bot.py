#!/usr/bin/env python3

import aiohttp
import asyncio
import discord
import sys

token_file = open('.bot.token', 'rt')
bot_token = token_file.read()
token_file.close()

client = discord.Client()
client.beer_watcher_running = False

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    chan = client.get_channel(891709147438010371)
    asyncio.get_event_loop().create_task(watch_beer_changes(chan))

drink_query_file = open('drink_query.graphql', 'rt')
drink_query = drink_query_file.read()
drink_query_file.close()

oktobeers_file = open('oktobeers.txt', 'rt')
oktobeers = oktobeers_file.read().lower().split('\n')
oktobeers_file.close()

async def get_drinks():
    async with aiohttp.ClientSession(headers = {'content-type': 'application/json'}) as session:
        async with session.post('https://ws.toasttab.com/opt-bff/v1/graphql',
            data=drink_query) as response:
            return await response.json()


async def get_draft_beer_lists():
    draft_beer_in_stock = []
    draft_beer_out_of_stock = []
    drinks = await get_drinks()
    for menu in drinks['data']['orderAtTableMenus']:
        if menu['id'] == '31a512c8-8d77-46b9-978e-1f7fc20a0be9' or menu['name'] == 'DRINK MENU':
            for group in menu['groups']:
                if group['guid'] == '78336a2a-bd4c-4f5a-8755-757043bc90a1' or group['name'] == 'DRAFT BEER':
                    for item in group['items']:
                        if item['outOfStock']:
                            draft_beer_out_of_stock.append(item['name'])
                        else:
                            draft_beer_in_stock.append(item['name'])

    return (draft_beer_in_stock, draft_beer_out_of_stock)

async def get_beer_changes(chan):
    old_draft_beer_in_stock = []
    old_draft_beer_out_of_stock = []
    while True:
        await asyncio.sleep(60)
        try:
            draft_beer_in_stock, draft_beer_out_of_stock = await get_draft_beer_lists()
        except Exception:
            continue

        if len(old_draft_beer_in_stock) or len(old_draft_beer_out_of_stock):
            for beer in draft_beer_in_stock:
                if not beer in old_draft_beer_in_stock:
                    for oktobeer in oktobeers:
                        if oktobeer in beer.lower():
                            await chan.send('@everyone {} IS A NEW OKTOBEERFEST BEER ON TAP'.format(beer))
                            break
                            break
                    else:        
                        await chan.send('{} is now on tap'.format(beer))
                
            for beer in draft_beer_out_of_stock:
                if not beer in old_draft_beer_out_of_stock:
                    await chan.send('{} is tapped out'.format(beer))
            
        old_draft_beer_in_stock = draft_beer_in_stock
        old_draft_beer_out_of_stock = draft_beer_out_of_stock
        

async def watch_beer_changes(chan):
    if client.beer_watcher_running:
        return
    await get_beer_changes(chan)

client.run(bot_token)
