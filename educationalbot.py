import sqlite3
import random
from datetime import date
from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import Application,CommandHandler,MessageHandler,CallbackQueryHandler,filters,ContextTypes
from telegram.ext import ApplicationBuilder

def init_db():
	conn=sqlite3.connect('pro_education.db')
	cursor=conn.cursor()
	cursor.execute('CREATE TABLE IF NOT EXISTS lessons (grade TEXT,subject TEXT,link TEXT)')
	cursor.execute('CREATE TABLE IF NOT EXISTS quizzes (grade TEXT,subject TEXT,question TEXT,options TEXT,correct_id INTEGER)')
	cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY,last_grade TEXT,last_active DATE)')
	cursor.execute('CREATE TABLE IF NOT EXISTS bookmarks (user_id INTEGER,link TEXT,title TEXT)')
	cursor.execute('CREATE TABLE IF NOT EXISTS quiz_stats (user_id INTEGER,solved_at DATE)')
	conn.commit()
	conn.close()

async def log_activity(user_id):
	today=date.today().isoformat()
	conn=sqlite3.connect('pro_education.db')
	cursor=conn.cursor()
	cursor.execute("INSERT INTO users (user_id,last_active) VALUES (?,?) ON CONFLICT (user_id) DO UPDATE SET last_active=excluded.last_active",(user_id,today))
	conn.commit()
	conn.close()

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
	user_id=update.effective_user.id
	await log_activity(user_id)
	keyboard=[[InlineKeyboardButton("📚သင်ခန်းစာများ📚",callback_data="menu_lessons"),InlineKeyboardButton("❤Bookmarks❤",callback_data="menu_bookmarks")],[InlineKeyboardButton("🗂Analytics🗂",callback_data="menu_analytics"),InlineKeyboardButton("🕯Help🕯",callback_data="menu_help")]]
	text="🎊Welcome to your educational assistant bot🎊\n\n သင်ခန်းစာများကိုလေ့လာရန်နှင့်အခြားfeaturesများအားရွေးချယ်အသုံးပြုနိုင်သည်"
	if update.message:
		await update.message.reply_text(text,reply_markup=InlineKeyboardMarkup(keyboard),parse_mode='Markdown')
	else:
		await update.callback_query.edit_message_text(text,reply_markup=InlineKeyboardMarkup(keyboard),parse_mode='Markdown')

async def menu_handler(update:Update,context:ContextTypes.DEFAULT_TYPE):
	query=update.callback_query
	data=query.data
	user_id=query.from_user.id
	await query.answer()
	if data=="menu_lessons" or data=="back_grades":
		keyboard=[[InlineKeyboardButton("📖Grade10📖",callback_data="grade_10")],[InlineKeyboardButton("📖Grade11📖",callback_data="grade_11")],[InlineKeyboardButton("📖Grade12📖",callback_data="grade_12")],[InlineKeyboardButton("🏡ပင်မစာမျက်နှာသို့🏡",callback_data="back_main")]]
		await query.edit_message_text("လေ့လာမယ့်အတန်းကိုရွေးချယ်ပါ",reply_markup=InlineKeyboardMarkup(keyboard))
	elif data.startswith("grade_"):
		grade=data.split("_")[1]
		conn=sqlite3.connect('pro_education.db')
		cursor=conn.cursor()
		cursor.execute("UPDATE users SET last_grade=? WHERE user_id=?",(grade,user_id))
		conn.commit()
		conn.close()
		subjects=["Myanmar","English","Math","Chemistry","Physics","Biology","Ecology","History","Geography"]
		keyboard=[]
		for i in range(0,len(subjects),2):
			row=[InlineKeyboardButton(subjects[i],callback_data=f"sub_{grade}_{subjects[i]}")]
			if i+1 < len(subjects):
				row.append(InlineKeyboardButton(subjects[i+1],callback_data=f"sub_{grade}_{subjects[i+1]}"))
			keyboard.append(row)
		keyboard.append([InlineKeyboardButton("🔙အတန်းပြန်ရွေးရန် 🔙",callback_data="back_grades")])
		await query.edit_message_text(f"📚Grade{grade}>ဘာသာရပ်ရွေးပါ",reply_markup=InlineKeyboardMarkup(keyboard))
	elif data.startswith("sub_"):
		parts=data.split("_")
		grade,subject=parts[1],parts[2]
		keyboard=[[InlineKeyboardButton("📚သင်ခန်းစာများ📚",callback_data=f"list_{grade}_{subject}")],[InlineKeyboardButton("💭Quuzဖြေရန်💭",callback_data=f"quiz_{grade}_{subject}")],[InlineKeyboardButton("🔙နောက်သို့🔙",callback_data=f"grade_{grade}")]]
		await query.edit_message_text(f"{subject}({grade})\n ဘာလုပ်ဆောင်လိုပါသလဲ?",reply_markup=InlineKeyboardMarkup(keyboard),parse_mode='Markdown')

async def show_lessons_list(update:Update,context:ContextTypes.DEFAULT_TYPE):
	query=update.callback_query
	parts=query.data.split("_")
	grade,subject=parts[1],parts[2]
	conn=sqlite3.connect('pro_education.db')
	cursor=conn.cursor()
	cursor.execute("SELECT link FROM lessons WHERE grade=? AND subject=?",(grade,subject))
	results=cursor.fetchall()
	conn.close()
	if results:
		text=f"📚{grade}({subject})သင်ခန်းစာများ \n\n"
		btns=[]
		for i,row in enumerate(results,1):
			link=row[0]
			text += f"{i}.[သင်ခန်းစာ{i}ကိုကြည့်ရန်]({link})\n"
			btns.append([InlineKeyboardButton(f"သင်ခန်းစာ{i}ကိုbookmarksထဲသိမ်းရန်",callback_data=f"save_{grade}_{subject}_{i}")])
		btns.append([InlineKeyboardButton("🔙နောက်သို့🔙",callback_data=f"sub_{grade}_{subject}")])
		await query.edit_message_text(text=text,reply_markup=InlineKeyboardMarkup(btns),parse_mode='Markdown',disable_web_page_preview=True)
	else:
		back_btn=[[InlineKeyboardButton("🔙နောက်သို့🔙",callback_data=f"sub_{grade}_{subject}")]]
		await query.edit_message_text(text=f"{subject} ({grade})အတွက်သင်ခန်းစာမရှိသေးပါ",reply_markup=InlineKeyboardMarkup(back_btn))

async def save_bookmark(update:Update,context:ContextTypes.DEFAULT_TYPE):
	query=update.callback_query
	await query.answer(text="လုပ်ဆောင်နေသည်..",show_alert=False)
	try:
		user_id=query.from_user.id
		data=query.data.split("_")
		grade,subject,index=data[1],data[2],data[3]
		conn=sqlite3.connect('pro_education.db')
		cursor=conn.cursor()
		cursor.execute("SELECT link FROM lessons WHERE grade=? AND subject=?",(grade,subject))
		res=cursor.fetchall()
		if res:
			target_link=res[int(index)-1][0]
			bookmark_data=f"G-{grade} {subject} ({index})|{target_link}"
			cursor.execute("INSERT INTO bookmarks (user_id,title) VALUES (?,?)",(user_id,bookmark_data))
		await query.answer(text="Bookmarkထဲသို့သိမ်းပြီးပါပြီ",show_alert=True)
		conn.commit()
		conn.close()
	except Exception as e:
		await query.answer(text=f"error:{str(e)}",show_alert=True)

async def show_bookmarks(update:Update,context:ContextTypes.DEFAULT_TYPE):
	query=update.callback_query
	user_id=query.from_user.id
	conn=sqlite3.connect('pro_education.db')
	cursor=conn.cursor()
	cursor.execute("SELECT title FROM bookmarks WHERE user_id=?",(user_id,))
	marks=cursor.fetchall()
	conn.close()
	if marks:
		text="✳မှတ်သားထားသောသင်ခန်းစာများ✳\n\n"
		btns=[]
		for m in marks:
			if "|" in m[0]:
				title_part,link_part=m[0].split("|")
				btns.append([InlineKeyboardButton(f"📔{title_part}ကိုကြည့်ရန်",url=link_part)])
			else:
				text+=f"\n. {m[0]}"
		btns.append([InlineKeyboardButton("⛺ပင်မစာမျက်နှာသို့⛺",callback_data="back_main")])
		await query.edit_message_text(text=text,reply_markup=InlineKeyboardMarkup(btns),parse_mode='Markdown')
	else:
		await query.edit_message_text("Bookmarkမှတ်ထားခြင်းမရှိပါ",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⛺ပင်မစာမျက်နှာသို့⛺",callback_data="back_main")]]))

async def show_quiz(update:Update,context:ContextTypes.DEFAULT_TYPE):
	query=update.callback_query
	parts=query.data.split("_")
	grade,subject=parts[1],parts[2]
	conn=sqlite3.connect('pro_education.db')
	cursor=conn.cursor()
	cursor.execute("SELECT question,options,correct_id FROM quizzes WHERE grade=? AND subject=? ORDER BY RANDOM() LIMIT 3",(grade,subject))
	questions=cursor.fetchall()
	conn.close()
	if len(questions)>0:
		await query.delete_message()
		for q_text,q_options,q_correct in questions:
			await context.bot.send_poll(chat_id=query.message.chat_id,question=f"{subject} Quiz:{q_text}",options=q_options.split("|"),type=Poll.QUIZ,correct_option_id=int(q_correct),is_anonymous=False)
		conn=sqlite3.connect('pro_education.db')
		cursor.execute("INSERT INTO quiz_stats(user_id,solved_at) VALUES (?,?)",(query.from_user.id,date.today().isoformat()))
		conn.commit()
		conn.close()
		await context.bot.send_message(query.message.chat_id,"မေးခွန်းများဖြေဆိုပြီးပါက ပင်မစာမျက်နှာသို့ပြန်သွားနိုင်ပါသည်",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⛺ပင်မစာမျက်နှာသို့⛺",callback_data="back_main")]]))
	else:
		await query.edit_message_text("Quizများမရှိသေးပါ",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("နောက်သို့",callback_data=f"sub_{grade}_{subject}")]]))

async def track_channel_posts(update:Update,context:ContextTypes.DEFAULT_TYPE):
	post=update.channel_post
	if not post or not (post.text or post.caption):
		return
	text=post.text if post.text else post.caption
	link=f"https://t.me/{post.chat.username}/{post.message_id}"
	grade=next((g for g in ["10","11","12"] if f"#G{g}" in text),None)
	subject=next((s for s in ["Myanmar","English","Math","Chemistry","Physics","Biology","Ecology","History","Geography"] if f"#{s}" in text),None)
	if grade and subject:
		conn=sqlite3.connect('pro_education.db')
		cursor=conn.cursor()
		if "#Quiz" in text or "#quiz" in text:
			try:
				parts=text.split("|")
				q_text=parts[0].replace(f"#G{grade}","").replace(f"#{subject}","").replace("#Quiz","").strip()
				options=[]
				correct_id=0
				for i,opt in enumerate(parts[1:]):
					if "#Ans" in opt:
						correct_id=i
						options.append(opt.split("#Ans")[0].strip())
					else:
						options.append(opt.strip())
				cursor.execute("INSERT INTO quizzes VALUES (?,?,?,?,?)",(grade,subject,q_text,"|".join(options),correct_id))
			except:
				pass
		cursor.execute("INSERT INTO lessons VALUES (?,?,?)",(grade,subject,link))
		conn.commit()
		cursor.execute("SELECT user_id FROM users WHERE last_grade=?",(grade,))
		targeted_users=cursor.fetchall()
		conn.close()
		for user in targeted_users:
			try:
				msg=f"📞📞သင်ခန်းစာအသစ်တက်လာပြီနော်📞📞\nGrade{grade} {subject}ကိုလေ့လာနိုင်ပြီ\n{link}"
				await context.bot.send_message(chat_id=user[0],text=msg,parse_mode='Markdown')
			except:
				continue

async def show_analytics(update:Update,context:ContextTypes.DEFAULT_TYPE):
	query=update.callback_query
	today=date.today().isoformat()
	conn=sqlite3.connect('pro_education.db')
	cursor=conn.cursor()
	cursor.execute("SELECT COUNT (*) FROM users")
	total_users=cursor.fetchone()[0]
	cursor.execute("SELECT COUNT (*) FROM users WHERE last_active=?",(today,))
	daily_active=cursor.fetchone()[0]
	cursor.execute("SELECT COUNT (*) FROM quiz_stats WHERE solved_at=?",(today,))
	quiz_done=cursor.fetchone()[0]
	conn.close()
	text=f"Bot Analytics ({today})\n\n 👥စုစုပေါင်းuser:{total_users}\n 📅ယနေ့အသုံးပြုသူ:{daily_active}\n ⏳ယနေ့Quizဖြေဆိုသူ:{quiz_done} ကြိမ်"
	await query.edit_message_text(text,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⛺ပင်မသို့⛺",callback_data="back_main")]]),parse_mode='Markdown')

async def broadcast_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE):
	if update.effective_user.id!=6627099674 and update.effective_user.id!=7210481411:
		return
	args=context.args
	if len(args)<2:
		return
	grade,msg=args[0],"".join(args[1:])
	conn=sqlite3.connect('pro_education.db')
	cursor=conn.cursor()
	cursor.execute("SELECT user_id FROM users WHERE last_grade=?",(grade,))
	recipients=cursor.fetchall()
	conn.close()
	count=0
	for r in recipients:
		try:
			await context.bot.send_message(r[0],f"🔴Adminအကြောင်းကြားချက်🔴({grade})\n\n{msg}",parse_mode='Markdown')
			count+=1
		except:
			continue
	await update.message.reply_text(f"Grade{grade} မှ ကျောင်းသား {count} ယောက်ထံပို့ပြီးပါပြီ")

def main():
	init_db()
	app=ApplicationBuilder().token("your token").build()
	app.updater.proxy_url="https://proxy.server:3128"
	app.updater.get_updates_proxy_url="https://proxy.server:3128"
	app.add_handler(CommandHandler("start",start))
	app.add_handler(CommandHandler("broadcast",broadcast_cmd))
	app.add_handler(CallbackQueryHandler(start,pattern="back_main"))
	app.add_handler(CallbackQueryHandler(show_analytics,pattern="menu_analytics"))
	app.add_handler(CallbackQueryHandler(menu_handler,pattern="menu_lessons|back_grade|grade_|sub_"))
	app.add_handler(CallbackQueryHandler(show_lessons_list,pattern="list_"))
	app.add_handler(CallbackQueryHandler(show_quiz,pattern="quiz_"))
	app.add_handler(CallbackQueryHandler(show_bookmarks,pattern="menu_bookmarks"))
	app.add_handler(CallbackQueryHandler(save_bookmark,pattern="save_"))
	app.add_handler(CallbackQueryHandler(lambda u,c:u.callback_query.edit_message_text("အကူအညီအတွက်Adminသို့ဆက်သွယ်ပါ\n နေပြည်တော်အတွင်းစာသင်ဝိုင်းများစုံစမ်းလိုပညကAdmin၏cbတွင်လာရောက်မေးမြန်းနိုင်သည်",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⛺ပင်မစာမျက်နှာသို့⛺",callback_data="back_main")]])),pattern="menu_help"))
	app.add_handler(MessageHandler(filters.ChatType.CHANNEL,track_channel_posts))
	print("Professional Education Bot is now online..")
	app.run_polling()

main()
