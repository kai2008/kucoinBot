#!/usr/bin/env python
__author__ = 'chase.ufkes'

from kucoin.client import Client
from slackclient import SlackClient
import time
import json
import logging

logging.basicConfig(level=logging.INFO, filename="kucoin.log", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

with open("config/botConfig.json", "r") as fin:
    config = json.load(fin)

apiKey = str(config['apiKey'])
apiSecret = str(config['apiSecret'])
trade = config['trade']
currency = config['currency']
sellValuePercent = config.get('sellValuePercent', 4)
buyValuePercent = config.get('buyValuePercent', 4)
volumePercent = config.get('buyVolumePercent', 4)
buyDifference = config.get('buyDifference', 0)
extCoinBalance = config.get('extCoinBalance', 0)
checkInterval = config.get('checkInterval', 30)
initialSellPrice = config.get('initialSellPrice', 0)
tradeAmount = config.get('tradeAmount', 0)
channel = config['slackChannel']
token = config['slackToken']

# global constants
client = Client(apiKey, apiSecret)
volumePercent = volumePercent * .01
sellValuePercent = sellValuePercent * .01
buyValuePercent = buyValuePercent * .01
buyDifference = buyDifference * .01
tokenPair = currency.upper() + "-" + trade.upper()

def determine_sell_amount(balance):
    return round(balance * volumePercent,4)

def determine_buy_amount(balance):
    amount = round(balance * volumePercent * (1 / (1 - volumePercent) * 1 + buyDifference), 4)
    return amount

def determine_initial_buy_price(currentTicker):
    price = currentTicker - (currentTicker * buyValuePercent)
    return price

def determine_initial_sell_price(currentTicker):
    price = currentTicker + (currentTicker * sellValuePercent)
    return price

def get_oid(data):
    data = (data[0])
    return data[5]

def get_last_order(history):
    data = (history[0])
    print (data)
    print (data[0])

def post_slack(type):
    logging.info("Attempting to send message...")
    sc = SlackClient(token)
    text = type + " completed for " + currency
    sc.api_call(
        "chat.postMessage",
        channel=channel,
        text=text
    )


cycle = 0
while True:
    try:
        openOrders = (client.get_active_orders(tokenPair))
        if (openOrders['BUY']) and (openOrders['SELL']):
            logging.info(openOrders)
        else:
            for type in openOrders:
                try:
                    oid = get_oid(openOrders[type])
                    logging.info("Cancel order " + oid)
                    logging.info(client.cancel_order(tokenPair, oid, type))
                except:
                    logging.info ("Order type " + type + " completed")
                    if token:
                        post_slack(type)
            balance = client.get_coin_balance(currency)
            balance = (float(balance['balanceStr']) + float(extCoinBalance))
            currentTicker = (client.get_tick(tokenPair)['lastDealPrice'])
            buyAmount = determine_buy_amount(balance)
            buyPrice = determine_initial_buy_price(currentTicker)
            logging.info("setting buy of " + str(buyAmount) + " at " + str(buyPrice))
            logging.info (client.create_buy_order(tokenPair, buyPrice, buyAmount))
            sellAmount = determine_sell_amount(balance)
            sellPrice = determine_initial_sell_price(currentTicker)
            logging.info("setting sell of " + str(sellAmount) + " at " + str(sellPrice))
            logging.info (client.create_sell_order(tokenPair, sellPrice, sellAmount))
    except:
        logging.info ("Shit went sideways...")

    if cycle == 100:
        logging.info("Garbage collection")
        gc.collect()
        count = 0
    logging.info("Waiting " + str(checkInterval) + " for next cycle...")
    time.sleep(checkInterval)
