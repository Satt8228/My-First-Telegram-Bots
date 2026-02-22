import logging
import time
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder,CommandHandler,ContextTypes
token="enter bot token"
def get_gold_price():
        url="https://api.gold-api.com/price/XAU"
        headers={'User-Agent':'Mozilla/5.0'}
        try:
                response=requests.get(url,headers=headers,timeout=10)
                if response.status_code==200:
                        data=response.json()
                        price=data['price']
                        return price
                else:
                        return None
        except Exception as e:
                print(f"{e}")
                return None
async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("WELCOME FROM MY GOLD PRICE BOT!\n I>
async def gold(update:Update,context:ContextTypes.DEFAULT_TYPE):
        price=get_gold_price()
        if price:
                text=f"International gold price\n\n 1 oz:{price}USD"
        else:
                text="Can't get price right now!!!!"
        await update.message.reply_text(text)
app=ApplicationBuilder().token(token).build()
app.add_handler(CommandHandler('start',start))
app.add_handler(CommandHandler('gold',gold))
print('Bot is running.....')
app.run_polling()
