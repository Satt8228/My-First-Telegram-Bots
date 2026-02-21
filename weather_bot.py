import requests
from geopy.geocoders import Nominatim
from telegram import Update
from telegram.ext import ApplicationBuilder,CommandHandler,MessageHandler,filters,>
def get_coords(city_name):
        geolocator=Nominatim(user_agent="testing_app_541380")
        location=geolocator.geocode(city_name)
        if location:
                return location.latitude,location.longitude
        return None,none
def get_weather(lat,lon):
        url=f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon>
        response=requests.get(url)
        data=response.json()
        return data['current']
async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Min Ga Lr Pr.Type City's nam:(eg.Mandalay>
async def handle_message(update:Update,context:ContextTypes.DEFAULT_TYPE):
        city=update.message.text
        await update.message.reply_text(f"finding weather of {city} ")
        try:
                lat,lon=get_coords(city)
                if lat:                                                                                    weather=get_weather(lat,lon)
                        temp=weather['temperature_2m']
                        humidity=weather['relative_humidity_2m']
                        result=(f"city name : {city}\n temperature : {temp} °C \n >
                        await update.message.reply_text(result)
                else:
                        await update.message.reply_text("check spelling or not fou>
        except Exception as e:
                await update.message.reply_text(f"error:{str(e)}")
                print("Something wrong")
app=ApplicationBuilder().token("your-bot-token-here").b>
app.add_handler(CommandHandler("start",start))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND),handle_message))
print("wather bot is running")
app.run_polling()
