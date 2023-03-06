import telebot
# import config
import requests
import json
import pandas as pd
from ta.momentum import RSIIndicator
from telebot import types


bot = telebot.TeleBot()
global symbol_list
symbol_list = []

def find_bull_div(message):
    # Set the API endpoint and parameters
    bot.send_message(message.chat.id, 'Start of the finding Bullish divergence in your symbols')
    # list_string = "\n".join(item for item in symbol_list)
    # bot.send_message(message.chat.id, text=f"Current list contents:\n{list_string}\n")
    url = "https://api.binance.com/api/v3/klines"
    for symbol in symbol_list:
        params = {
            "symbol": symbol,
            "interval": "1h",
            "limit": "800"
        }

        # Make a request to the API endpoint
        response = requests.get(url, params=params)

        # Difference variable
        difference = 0.0

        # Parse the response into a pandas dataframe
        data = json.loads(response.text)
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time",
                                         "quote_asset_volume", "num_trades", "taker_buy_base_asset_volume",
                                         "taker_buy_quote_asset_volume", "ignore"])
        df = df.drop(columns=['volume', 'close_time', "quote_asset_volume", "num_trades", "taker_buy_base_asset_volume",
                              "taker_buy_quote_asset_volume", "ignore"])

        # Convert the close column to float type
        df["close"] = df["close"].astype(float)

        # Convert the timestamp to a readable date format
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        # Calculate RSI values using TA package
        rsi_period = 14
        df['rsi'] = RSIIndicator(df['close'], rsi_period).rsi()

        # Get the current and previous candles
        prev_candle = df.iloc[-2]
        curr_candle = df.iloc[-1]
        count = 0

        for i in range(1, 40):
            if float(curr_candle['high']) <= float(df.iloc[-i]['low']):  # check if current High <= previousLow
                if float(curr_candle['rsi']) > float(df.iloc[-i]['rsi']):
                    count += 1
                    if (float(curr_candle['rsi']) - float(df.iloc[-i]['rsi'])) > difference:
                        str = f"There is a bullish divergence in {symbol} with \nCurrent high = {curr_candle['high']} and Current RSI = {curr_candle['rsi']}\nThe candle on {df.iloc[-i]['timestamp']} \nwith Low = {df.iloc[-i]['low']} and RSI = {df.iloc[-i]['rsi']}\n"
                    # bot.send_message(message.chat.id, f"Bullish divergence with \nCurrent high = {curr_candle['high']} and Current RSI = {curr_candle['rsi']}\nThe candle on {df.iloc[-i]['timestamp']} \nwith Low = {df.iloc[-i]['low']} and RSI = {df.iloc[-i]['rsi']}\n")

        if count == 0:
            bot.send_message(message.chat.id, f'For now there is no Bullish divergence in {symbol}')
        else:
            bot.send_message(message.chat.id, str)



# def get_symbol(message):  # get symbol
#     symbol = message.text
#     symbol_list.append(symbol)
#     bot.send_message(message.chat.id, "Here is your symbols - {}".format(symbol_list), parse_mode='html')
#     # bot.register_next_step_handler(message, find_bull_div(message, symbol_list))

def add_symbol(message):  # add symbol
    # Check if symbol is available in binance
    responseS = requests.get('https://api.binance.com/api/v3/exchangeInfo')
    exchange_info = responseS.json()
    bot.send_message(message.chat.id, exchange_info)

    symbols = [symbolic['symbol'] for symbolic in exchange_info['symbols']]

    symbol = message.text

    if symbol in symbols:
        symbol_list.append(symbol)
        bot.send_message(message.chat.id, f"Symbol {symbol} is added to list!")
    else:
        bot.send_message(message.chat.id, f"Symbol {symbol} is not existed in a Binance")



def del_symbol(message):
    symbolDel = message.text
    if str(symbolDel) in symbol_list:
        symbol_list.remove(symbolDel)
        list_string = "\n".join(str(item) for item in symbol_list)
        bot.send_message(message.chat.id, text=f"Successfully deleted!\n\nCurrent list contents:\n{list_string}")
    else:
        bot.send_message(message.chat.id, text=f"There is no symbol with provided name")


def makeKeyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    itemSymbols = types.KeyboardButton('Selected symbols')
    itemAddSymbols = types.KeyboardButton('Add new symbol')
    itemDelSymbol = types.KeyboardButton('Delete an existing symbol')
    itemRunApp = types.KeyboardButton('Find bullish divergence in your symbols')

    markup.add(itemSymbols, itemAddSymbols, itemDelSymbol, itemRunApp)
    return markup


@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "Welcome, {0.first_name}! Use the buttons bellow to interact with me".format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=makeKeyboard())



@bot.message_handler(content_types=['text'])
def check_message(message):
    if message.chat.type == 'private':
        if message.text == 'Selected symbols':
            if len(symbol_list) == 0:
                bot.send_message(message.chat.id, text="Your list is currently empty.")
            else:
                list_string = "\n".join(str(item) for item in symbol_list)
                bot.send_message(message.chat.id, text=f"Current list contents:\n{list_string}")
            # bot.send_message(message.chat.id, "Here is your symbols - {}".format(symbol_list))
        elif message.text == 'Find bullish divergence in your symbols':
            find_bull_div(message)
        elif message.text == 'Add new symbol':
            msg = bot.send_message(message.chat.id, "Write a symbol that you want to add")
            bot.register_next_step_handler(msg, add_symbol)
            # symb = message.text
            # symbol_list.append(symb)
            # bot.send_message(message.chat.id, f"Symbol {symb} added to list!")
        elif message.text == 'Delete an existing symbol':
            if len(symbol_list) == 0:
                bot.send_message(message.chat.id, text="Your list is currently empty.")
            else:
                list_string = "\n".join(str(item) for item in symbol_list)
                msg = bot.send_message(message.chat.id, text=f"Current list contents:\n{list_string}\n\nEnter the symbol name that you want to delete from your list.")
                bot.register_next_step_handler(msg, del_symbol)
        else:
            bot.send_message(message.chat.id, 'Please use buttons to interact with me')



bot.polling(none_stop=True)

