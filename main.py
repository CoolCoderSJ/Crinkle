import web
from replit import db
import os
from requests import get
from user_agents import parse
import pytz
from datetime import datetime
import random
from discord_webhook import DiscordWebhook
from bs4 import BeautifulSoup 
import shutil
import requests
import sqlite3

os.system("clear")


render = web.template.render('templates/')
urls = (
	'/l/(.*)', 'short',
	'/add', 'add',
	'/', 'index',
	'/dash', 'index',
	'/edit/(.*)', 'edit',
	'/edit', 'edit2',
	'/delete', 'delete',
	'/details', 'url_info',
	'/info/(.*)/(.*)', 'public_info',
  	'/demo', 'demo',
	'/qrcode', 'qrcode',
	'/qrcode/view/(.*)', 'qrcodeview',
	'/shortweb', 'shortweb',
	'/namec', 'namec',
	'/login', 'login',
	'/signup', 'signup',
	'/bot/guild', 'botg',
	'/bot/dm', 'botd',
	'/bot_info', "bot_info",
	'/bmlet', 'bmlet',
	'/sitemap', 'sitemap',
	'/(.*)', 'short2'
	)

#os.system("clear")	

app = web.application(urls, locals())
session = web.session.Session(app, web.session.DiskStore('sessions'))  
def notfound():
	return web.notfound(render.notfound())

class sitemap:
	def GET(self):
		return render.sitemap()

class bmlet:
	def GET(self):
		post_input = web.input(_method='post')
		post_input = list(post_input)
		i = web.input()
		short = i.short
		url = i.url
		if i.token == "188b28e3da5d553300ceb9203fe65a5ddf83af76e9e591ade809d0848f230b1b":
			if short == "null" or short == "":
				letters = ["a","b",	"c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
				#Generate a 6 letter backend, you will only run out of 6 letter backends if you auto generate more than 46656 backends.
				tries = 0
				num = 1
				for l in range(num):
					letter = random.choice(letters)
					short = short+letter
				tries = 1
				while short in db:
					for l in range(num):
						letter = random.choice(letters)
						short = short+letter
					tries += 1
					total5 = 1
					for x in range(num):
						total5 = total5*num
					if tries == total5:
						num += 1
			if short not in db:
				db[short] = url
				conn = sqlite3.connect('database.db')
				db2 = conn.cursor()
				db2.execute(f"INSERT into backends (short, name, webhook, agents, user) VALUES ('{short}', 'NONE', 'NONE', 'NONE', 'CoolCoderSJ')")
				conn.commit()
				db2.close()
				import json
				web.header('Content-Type', 'application/json')
				web.header('Access-Control-Allow-Origin', '*')
				web.header('Access-Control-Allow-Credentials', 'true')
				web.header('Access-Control-Allow-Methods', 'GET')
				web.header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
				return json.dumps({"BACKEND":short})
			return "No."



class botg:
	def POST(self):
		post_input = web.input(_method='post')
		post_input = list(post_input)
		print(post_input, web.ctx.env)
		for item in post_input:
			if item.split(":")[0] == "URL":
				url = item.split(":")[-1]
			if item.split(":")[0] == "SHORT":
				short = item.split(":")[-1]
		if short == "":
			letters = ["a","b",	"c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
			#Generate a 6 letter backend, you will only run out of 6 letter backends if you auto generate more than 46656 backends.
			tries = 0
			num = 1
			for l in range(num):
				letter = random.choice(letters)
				short = short+letter
			tries = 1
			while short in db:
				for l in range(num):
					letter = random.choice(letters)
					short = short+letter
				tries += 1
				total5 = 1
				for x in range(num):
					total5 = total5*num
				if tries == total5:
					num += 1
		if short not in db:
			db[short] = url
			conn = sqlite3.connect('database.db')
			db2 = conn.cursor()
			db2.execute(f"INSERT into backends (short, name, webhook, agents, user) VALUES ('{short}', 'NONE', 'NONE', 'NONE', 'EXTERNAL')")
			conn.commit()
			db2.close()
			return short
		return False

class botd:
	def POST(self):
		post_input = web.input(_method='post')
		post_input = list(post_input)
		print(post_input)
	
		for item in post_input:
			if item.split(":")[0] == "URL":
				url = item.split(":")[-1]
			if item.split(":")[0] == "SHORT":
				short = item.split(":")[-1]
		if short == "":
			letters = ["a","b",	"c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
			#Generate a 6 letter backend, you will only run out of 6 letter backends if you auto generate more than 46656 backends.
			tries = 0
			num = 1
			for l in range(num):
				letter = random.choice(letters)
				short = short+letter
			tries = 1
			while short in db:
				for l in range(num):
					letter = random.choice(letters)
					short = short+letter
				tries += 1
				total5 = 1
				for x in range(num):
					total5 = total5*num
				if tries == total5:
					num += 1
		if short not in db:
			conn = sqlite3.connect('database.db')
			db2 = conn.cursor()
			db2.execute(f"INSERT into backends (short, name, webhook, agents, user) VALUES ('{short}', 'NONE', 'NONE', 'NONE', 'EXTERNAL')")
			conn.commit()
			db2.close()
			return short
		return False


class bot_info:
	def POST(self):
		#os.system("clear")	
		conn = sqlite3.connect('database.db')
		db2 = conn.cursor()
		query = db2.execute(f"SELECT * from backends").fetchall()
		db2.close()
		users2 = {}
		for url in query:
			users2[url[1]] = url[5]
		i = web.input(_method="post")
		print(i)
		s = i.short
		if s in db:
			user = users2[s]
			conn = sqlite3.connect('database.db')
			db2 = conn.cursor()
			query = db2.execute(f"SELECT * from backends WHERE short = '{s}'").fetchall()
			db2.close()
			import ast
			query = ast.literal_eval(query[0][4])
			if query != 'NONE':
				clicks = 0
				chrome = 0
				ff = 0
				safari = 0
				opera = 0
				edge = 0
				mac = 0
				ipad = 0
				android = 0
				windows7 = 0
				windows10 = 0
				apple = 0
				linux = 0
				chromeos= 0 
				conn = sqlite3.connect('database.db')
				db2 = conn.cursor()
				query = db2.execute(f"SELECT * from backends WHERE short = '{s}'").fetchall()
				db2.close()
				import ast
				query = ast.literal_eval(query[0][4])
				for line in query:
					clicks += 1
					if "Chrome" in line:
						chrome += 1
					if "Firefox" in line:
						ff += 1
					if "Safari" in line:
						safari += 1
					if "Opera" in line:
						opera += 1
					if "Edge" in line:
						edge += 1
					if "Mac" in line:
						mac += 1
					if "iPad" in line:
						ipad += 1
					if "Android" in line:
						android += 1
					if "Windows  10" in line:
						windows10 += 1
					if "Windows  7" in line:
						windows7 += 1
					if "Apple" in line:
						apple += 1
					if "Linux" in line:
						linux += 1
					if "Chrome OS" in line:
						chromeos += 1
				dev2 = [chrome, ff, safari, opera, edge, mac, ipad, android, windows7, windows10, apple, 
				linux, chromeos]
				dev = ""
				for thing in dev2:
					sep = ","
					dev = str(dev)+sep+str(thing)
				tots = str(clicks)+"|"+dev
			return tots
		return False


class login:
	def GET(self):
		##os.system("clear")	
		i = web.input(code=0)
		msg = ""
		if i.code == "1":
			msg = "An error occurred while logging you in. Please try again or contact a deveoper."
		return render.login(msg)
		##os.system("clear")	
		 
	def POST(self):
		##os.system("clear")	
		i = web.input()
		r = requests.post("https://sjauth.coolcodersj.repl.co/apil", data={"user":i.user, "passw":i.passw, "cn":"SJURL"})
		if r.text == "True":
			web.setcookie("logged_in", True)
			web.setcookie("user", i.user)
			raise web.seeother("/")
		else:
			raise web.seeother("/login?code=1")
		##os.system("clear")	
		 

class signup:
	def GET(self):
		##os.system("clear")
		i = web.input(code=0)
		msg = ""
		if i.code == "1":
			msg = "An error occurred while signing you up. Please try again or contact a deveoper."	
		return render.signup(msg)
		##os.system("clear")	
		 
	def POST(self):
		##os.system("clear")	
		i = web.input()
		r = requests.post("https://sjauth.coolcodersj.repl.co/apisi", data={"user":i.user, "passw":i.passw, "cn":"SJURL"})
		if r.text == "True":
			web.setcookie("logged_in", True)
			web.setcookie("user", i.user)
			raise web.seeother("/")
		else:
			raise web.seeother("/signup?code=1")
		##os.system("clear")	
		 


class logout:
	def GET(self):
		#os.system("clear")	
		web.setcookie('logged_in', '', expires=-1)
		web.setcookie('user', '', expires=-1)
		raise web.seeother("/")
		#os.system("clear")	
		 

class shortweb:
	def POST(self):
		user = web.cookies().get("user")
		#os.system("clear")	
		i = web.input()
		short = i.short
		conn = sqlite3.connect('database.db')
		db2 = conn.cursor()
		query = db2.execute(f"SELECT * from backends WHERE short = '{short}'").fetchall()
		db2.close()
		query = query[0]
		if query[3] != 'NONE':
			conn = sqlite3.connect('database.db')
			db2 = conn.cursor()
			db2.execute(f"UPDATE backends SET webhook = 'NONE' WHERE short = '{short}'")
			conn.commit()
			db2.close()
		else:
			conn = sqlite3.connect('database.db')
			db2 = conn.cursor()
			db2.execute(f"UPDATE backends SET webhook = '{i.webhook}' WHERE short = '{short}'")
			conn.commit()
			db2.close()
		raise web.seeother("/")
		#os.system("clear")	

		 

class namec:
	def POST(self):
		#os.system("clear")	
		if web.cookies().get("logged_in"):
			i = web.input()
			name = i.name
			short = i.short
			user = web.cookies().get("user")
			conn = sqlite3.connect('database.db')
			db2 = conn.cursor()
			query = db2.execute(f"SELECT * from backends WHERE short = '{short}'").fetchall()
			db2.close()
			query = query[0]
			if name == '':
				conn = sqlite3.connect('database.db')
				db2 = conn.cursor()
				db2.execute(f"UPDATE backends SET name = 'NONE' WHERE short = '{short}'")
				conn.commit()
				db2.close()
			else:
				conn = sqlite3.connect('database.db')
				db2 = conn.cursor()
				db2.execute(f"UPDATE backends SET name = '{name}' WHERE short = '{short}'")
				conn.commit()
				db2.close()
			raise web.seeother("/")
		else:
			raise web.seeother("https://promo.sjurl.repl.co")
		#os.system("clear")	


			

class short2:
	def GET(self, short):
		#os.system("clear")	
		if short != "" and short != "add" and short != "details" and short != "edit" and not short.startswith("edit") and not short.startswith("l") and short != "demo" and short != "qrcode" and not short.startswith("qrcode/view") and short != "unshortr":
			raise web.seeother("/l/"+short)
		#os.system("clear")	

		 

class qrcode:
	def POST(self):
		#os.system("clear")	
		if web.cookies().get("logged_in"):
			import pyqrcode 
			import png 
			from pyqrcode import QRCode 
			i = web.input()
			short = "https://sjurl.repl.co/l/"+i.short
			qr = pyqrcode.create(short)
			qr.png("static/images/qr/"+i.short+'.png', scale = 6) 
			raise web.seeother("/")
		else:
			raise web.seeother("https://promo.sjurl.repl.co")
		#os.system("clear")	
		 
 
class qrcodeview:
	def GET(self, qrcode):
		#os.system("clear")	
		if web.cookies().get("logged_in"):
			return render.qrcodeview(qrcode)
		else:
			raise web.seeother("https://promo.sjurl.repl.co")
		#os.system("clear")	
		 

		
class short:
	def GET(self, short):
		if short == "/" or short == "" or short == "favicon.ico":
			raise web.seeother('/dash')
		conn = sqlite3.connect('database.db')
		db2 = conn.cursor()
		query = db2.execute(f"SELECT * from backends").fetchall()
		db2.close()
		user = {}
		for url in query:
			user[url[1]] = url[5]
		if short.endswith("+"):
				short1 = short.split("+")[-2]
				url = db[short1]
				if not url.startswith("http"):
					url = "http://"+url
				r = get(url) 
				soup = BeautifulSoup(r.text, 'html.parser') 
				titles = ""
				for title in soup.find_all('title'): 
					titles += str(title)+"\n"
				user = user[short1]
				conn = sqlite3.connect('database.db')
				db2 = conn.cursor()
				query = db2.execute(f"SELECT * from backends WHERE short = '{short1}'").fetchall()
				db2.close()
				name = query[0][2]
				return render.sneak(short1, url, titles, name)
		#os.system("clear")	
		#os.system("clear")	
		if short.split("/")[0] in db or short.split("#")[0] in db or short.split("?")[0]:
			if short.split("/")[0] in db:
				params = short.split(short.split("/")[0])
				params = "".join(params)
			elif short.split("#")[0] in db:
				params = short.split(short.split("#")[0])
				params = "".join(params)
			elif short.split("?")[0] in db:
				params = short.split(short.split("?")[0])
				params = "".join(params)
			else:
				params = ""
			tz_NY = pytz.timezone('America/New_York') 
			now = datetime.now(tz_NY)
			dt_string = now.strftime("%m/%d/%Y %H:%M:%S")
			short1 = short.split("/")[0]
			usr_str = web.ctx.env['HTTP_USER_AGENT']
			usr_agent2 = parse(usr_str)
			usr_agent = ""
			if usr_agent2.browser.family != None:
				bfamily = usr_agent2.browser.family
			else:
				bfamily = ""
			if usr_agent2.browser.version_string != None:
				bversion = usr_agent2.browser.version_string
			else:
				bversion = ""

			if usr_agent2.os.family != None:
				osfamily = usr_agent2.os.family
			else:
				osfamily = ""
			if usr_agent2.os.version_string != None:
				osversion = usr_agent2.os.version_string
			else:
				osversion = ""

			if usr_agent2.device.brand != None:
				devbrand = usr_agent2.device.brand
			else:
				devbrand = ""
			if usr_agent2.device.family != None:
				devfamily = usr_agent2.device.family
			else:
				devfamily = ""
			if usr_agent2.device.model != None:
				devmodel = usr_agent2.device.model
			else:
				devmodel = ""
			usr_agent = bfamily + "  " + bversion + "  " + osfamily + "  " + osversion + "  " + devbrand + "  " + devfamily + "  " + devmodel + "  EST TIME:  " + dt_string
			line = usr_agent
			conn = sqlite3.connect('database.db')
			db2 = conn.cursor()
			query = db2.execute(f"SELECT * from backends WHERE short = '{short1}'").fetchall()
			db2.close()
			query = query[0]
			import ast
			if query[4] == 'NONE':
				agents = []
			else:
				agents = ast.literal_eval(query[4])
			agents.append(line)

			conn = sqlite3.connect('database.db')
			db2 = conn.cursor()
			query = db2.execute(f"""UPDATE backends SET agents = "{agents}" WHERE short = '{short1}'""")
			conn.commit()
			db2.close()
		

			url = db[short1]
			if not url.startswith("https://"):
				url = "https://"+url
			conn = sqlite3.connect('database.db')
			db2 = conn.cursor()
			query = db2.execute(f"SELECT * from backends WHERE short = '{short}'").fetchall()
			db2.close()
			query = query[0]
			if query[3] != 'NONE':
				webhookurl = query[3]
				webhook = DiscordWebhook(url=webhookurl, content="A Link was visited. \n\nDetails:\nShortened Backend: "+short+"\nFull URL: "+url+"\nDevice details: "+bfamily + "  " + bversion + "  " + osfamily + "  " + osversion + "  " + devbrand + "  " + devfamily + "  " + devmodel+"\n\nTime: "+dt_string)
				webhook.execute()
			raise web.seeother(url+params)
		else:
			raise web.notfound()
		#os.system("clear")	
		 
    
class add:
	def GET(self):
		#os.system("clear")	
		if web.cookies().get("logged_in"):
			idk = ""
			return render.add(db, idk)
		else:
			raise web.seeother("https://promo.sjurl.repl.co")
		#os.system("clear")	
		 
	def POST(self):
		user = web.cookies().get("user")
		#os.system("clear")	
		i = web.input()
		short=i.short
		if short == "":
			#pass a list of letters
			letters = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
			#Generate a 6 letter backend, you will only run out of 6 letter backends if you auto generate more than 46656 backends.
			tries = 0
			for l in range(6):
				letter = random.choice(letters)
				short = short+letter
			tries = 1
			num = 6
			while short in db:
				for l in range(num):
					letter = random.choice(letters)
					short = short+letter
				tries += 1
				if tries == 46656:
					num += 1
		if "webhook" in i:
			webhookurl = i.webhook
		else:
			webhookurl = "NONE"
		url = i.url
		name = i.name
		if name == "":
			name = 'NONE'
		if short not in db:
			conn = sqlite3.connect('database.db')
			db2 = conn.cursor()
			query = db2.execute(f"INSERT into backends (short, name, webhook, agents, user) VALUES ('{short}', '{name}', '{webhookurl}', 'NONE', '{user}')")
			conn.commit()
			db2.close()
			db[short] = url
			return render.success(short, url)
		else:
			return render.alert()
		#os.system("clear")	
		 

class index:
	def GET(self):
		#os.system("clear")
		if web.cookies().get("logged_in"):
			user = web.cookies().get("user")
			passw = ""
			shortwebs = []
			names = {}
			userlinks = {}
			for short in db:
				if short != "/":
					name = ""
					conn = sqlite3.connect('database.db')
					db2 = conn.cursor()
					query = db2.execute(f"SELECT * from backends WHERE short = '{short}'").fetchall()
					db2.close()
					query = query[0]
					if query[3] != 'NONE':
						shortwebs.append(short)
					conn = sqlite3.connect('database.db')
					db2 = conn.cursor()
					query = db2.execute(f"SELECT * from backends WHERE short = '{short}'").fetchall()
					db2.close()
					query = query[0]
					if query[2] != 'NONE':
						name = query[2]
					else:
						name = ""
					names[short] = name

			conn = sqlite3.connect('database.db')
			db2 = conn.cursor()
			query = db2.execute(f"SELECT short from backends WHERE user = '{user}'").fetchall()
			db2.close()
			for link in query:
				userlinks[link[0]] = db[link[0]]
			return render.index(userlinks, passw, shortwebs, names)
		else:
			raise web.seeother("https://promo.sjurl.repl.co")
		#os.system("clear")	
class edit:
	def GET(self, short):
		#os.system("clear")	
		if web.cookies().get("logged_in"):
			user = web.cookies().get("user")
			conn = sqlite3.connect('database.db')
			db2 = conn.cursor()
			query = db2.execute(f"SELECT * from backends WHERE short = '{short}'").fetchall()
			user2 = query[0][-1]
			print(user, user2)
			if user2 == user:
				passw = ""
				return render.edit(db, short, passw)
			else:
				raise web.seeother('/')
		else:
			raise web.seeother("https://promo.sjurl.repl.co")
		#os.system("clear")	
		 

class edit2:
	def POST(self):
		#os.system("clear")	
		if web.cookies().get("logged_in"):
			i = web.input()
			newurl = i.newurl
			short = i.short
			db[short] = newurl
			raise web.seeother('/')
		else:
			raise web.seeother("https://promo.sjurl.repl.co")
		#os.system("clear")	
		 

class delete:
	def POST(self):
		#os.system("clear")	
		user = web.cookies().get("user")
		if web.cookies().get("logged_in"):
			i = web.input()
			short = i.short
			
			if os.path.exists("static/images/qr/"+short+".png"):
				os.remove("static/images/qr/"+short+".png")	
			conn = sqlite3.connect('database.db')
			db2 = conn.cursor()
			query = db2.execute(f"DELETE from backends WHERE short = '{short}'")
			conn.commit()
			db2.close()
			del db[short]
			raise web.seeother('/')
		else:
			raise web.seeother("https://promo.sjurl.repl.co")
		#os.system("clear")	
		 

class url_info:
	def POST(self):
		#os.system("clear")	
		user = web.cookies().get("user")
		if web.cookies().get("logged_in"):
			agent = []
			i = web.input()
			s = i.short
			conn = sqlite3.connect('database.db')
			db2 = conn.cursor()
			query = db2.execute(f"SELECT * from backends WHERE short = '{s}'").fetchall()
			conn.commit()
			db2.close()
			import ast
			if query[0][4] == "NONE":
					query = []
			else:
				query = ast.literal_eval(query[0][4])
			if query != 'NONE':
				clicks = 0
				chrome = 0
				ff = 0
				safari = 0
				opera = 0
				edge = 0
				mac = 0
				ipad = 0
				android = 0
				windows7 = 0
				windows10 = 0
				apple = 0
				linux = 0
				chromeos= 0 
				conn = sqlite3.connect('database.db')
				db2 = conn.cursor()
				query = db2.execute(f"SELECT * from backends WHERE short = '{s}'").fetchall()
				conn.commit()
				db2.close()
				import ast
				if query[0][4] == "NONE":
					query = []
				else:
					query = ast.literal_eval(query[0][4])
				for line in query:
					agent.append(line)
					clicks += 1
					if "Chrome" in line:
						chrome += 1
					if "Firefox" in line:
						ff += 1
					if "Safari" in line:
						safari += 1
					if "Opera" in line:
						opera += 1
					if "Edge" in line:
						edge += 1
					if "Mac" in line:
						mac += 1
					if "iPad" in line:
						ipad += 1
					if "Android" in line:
						android += 1
					if "Windows  10" in line:
						windows10 += 1
					if "Windows  7" in line:
						windows7 += 1
					if "Apple" in line:
						apple += 1
					if "Linux" in line:
						linux += 1
					if "Chrome OS" in line:
						chromeos += 1
				dev = [chrome, ff, safari, opera, edge, mac, ipad, android, windows7, windows10, apple, 
				linux, chromeos]
			return render.details(agent, clicks, dev, s)
		else:
			raise web.seeother("https://promo.sjurl.repl.co")
		#os.system("clear")	

class public_info:
	def GET(self, s, option):
		#os.system("clear")	
		options = []
		if "221" in option:
			options.append("clicks")
		if "324" in option:
			options.append("table")
		if "239" in option:
			options.append("agents")
		if "692" in option:
			options.append("times")
		user = web.cookies().get("user")
		agent = []
		i = web.input()
		conn = sqlite3.connect('database.db')
		db2 = conn.cursor()
		query = db2.execute(f"SELECT * from backends WHERE short = '{s}'").fetchall()
		conn.commit()
		db2.close()
		import ast
		if query[0][4] == "NONE":
				query = []
		else:
			query = ast.literal_eval(query[0][4])
		if query != 'NONE':
			clicks = 0
			chrome = 0
			ff = 0
			safari = 0
			opera = 0
			edge = 0
			mac = 0
			ipad = 0
			android = 0
			windows7 = 0
			windows10 = 0
			apple = 0
			linux = 0
			chromeos= 0 
			conn = sqlite3.connect('database.db')
			db2 = conn.cursor()
			query = db2.execute(f"SELECT * from backends WHERE short = '{s}'").fetchall()
			conn.commit()
			db2.close()
			import ast
			if query[0][4] == "NONE":
				query = []
			else:
				query = ast.literal_eval(query[0][4])
			for line in query:
				agent.append(line)
				clicks += 1
				if "Chrome" in line:
					chrome += 1
				if "Firefox" in line:
					ff += 1
				if "Safari" in line:
					safari += 1
				if "Opera" in line:
					opera += 1
				if "Edge" in line:
					edge += 1
				if "Mac" in line:
					mac += 1
				if "iPad" in line:
					ipad += 1
				if "Android" in line:
					android += 1
				if "Windows  10" in line:
					windows10 += 1
				if "Windows  7" in line:
					windows7 += 1
				if "Apple" in line:
					apple += 1
				if "Linux" in line:
					linux += 1
				if "Chrome OS" in line:
					chromeos += 1
			dev = [chrome, ff, safari, opera, edge, mac, ipad, android, windows7, windows10, apple, 
			linux, chromeos]
			if not "times" in options:
				agent = []
				for line in query:
					e = line.split("EST")[0]
					agent.append(e)
		return render.public(agent, clicks, dev, options)

		#os.system("clear")	 	 

class demo:
	def GET(self):
		return render.demo()
		#os.system("clear")	
	def POST(self):
		user = "EXTERNAL"
		#os.system("clear")	
		i = web.input()
		short=i.short
		if short == "":
			#pass a list of letters
			letters = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
			#Generate a 6 letter backend, you will only run out of 6 letter backends if you auto generate more than 46656 backends.
			tries = 0
			for l in range(6):
				letter = random.choice(letters)
				short = short+letter
			tries = 1
			num = 6
			while short in db:
				for l in range(num):
					letter = random.choice(letters)
					short = short+letter
				tries += 1
				if tries == 46656:
					num += 1
		if "webhook" in i:
			webhookurl = i.webhook
		else:
			webhookurl = "NONE"
		url = i.url
		name = i.name
		if name == "":
			name = 'NONE'
		if short not in db:
			conn = sqlite3.connect('database.db')
			db2 = conn.cursor()
			query = db2.execute(f"INSERT into backends (short, name, webhook, agents, user) VALUES ('{short}', '{name}', '{webhookurl}', 'NONE', '{user}')")
			conn.commit()
			db2.close()
			db[short] = url
			return render.success(short, url)
		else:
			return render.alert()
		#os.system("clear")	
		 


if __name__ == "__main__":
	app.notfound = notfound
	app.run()
