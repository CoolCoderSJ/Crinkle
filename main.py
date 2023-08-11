#url shortener
from flask import Flask, render_template, request, redirect, session, abort
from flask_session import Session
import random, string, datetime, requests, os
from argon2 import PasswordHasher
ph = PasswordHasher()

from dotenv import load_dotenv
load_dotenv()

from urllib.parse import urlparse

from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.query import Query
from appwrite.services.users import Users

from user_agents import parse #https://pypi.org/project/user-agents/

client = (Client()
    .set_endpoint('https://appwrite.shuchir.dev/v1') 
    .set_project('crkl')               
    .set_key(os.environ['APPWRITE']))   
db = Databases(client)
users = Users(client)

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


def get_all_docs(data, collection, queries=[]):
    docs = []
    offset = 0
    queries.append(Query.offset(offset))
    queries.append(Query.limit(100))
    while True:
        results = db.list_documents(data, collection, queries=queries)
        if len(docs) == results['total']:
            break
        results = results['documents']
        docs += results
        offset += len(results)
    return docs

@app.route('/')
def index():
    if "user" not in session:
        return render_template('landing.html')
    user = session['user']
    if not user: return render_template('landing.html')
    links = get_all_docs('data', 'urls', queries=[Query.equal("userid", user)])
    return render_template('index.html', links=links)

@app.route('/shorten', methods=['POST'])
def shorten():
    url = request.form['url']
    if "shortkey" not in request.form:
        shortkey = ''.join(random.choice(string.ascii_letters) for i in range(6))
    elif not request.form['shortkey']:
        shortkey = ''.join(random.choice(string.ascii_letters) for i in range(6))
    else:
        shortkey = request.form['shortkey']
    
    if "password" not in request.form:
        password = ''
    elif not request.form['password']:
        password = ''
    else:
        password = request.form['password']
    user = session['user']
    if not user:
        return abort(401)
    if not url:
        return abort(400)
    db_results = db.list_documents('data', 'urls', queries=[Query.equal("shortkey", shortkey)])
    if db_results['total'] > 0:
        return abort(409)
    data = {
        'url': url,
        'shortkey': shortkey,
        'userid': user
    }
    if password: data['password'] = ph.hash(password)
    db.create_document('data', 'urls', "unique()", data)
    return redirect('/dashboard/'+shortkey)

@app.route("/edit", methods=['POST'])
def edit():
    url = request.form['url']
    shortkey = request.form['old_shortkey']

    if "new_shortkey" not in request.form:
        new_shortkey = ''.join(random.choice(string.ascii_letters) for i in range(6))
    elif not request.form['new_shortkey']:
        new_shortkey = ''.join(random.choice(string.ascii_letters) for i in range(6))
    else:
        new_shortkey = request.form['new_shortkey']

    if "password" not in request.form:
        password = ''
    elif not request.form['password']:
        password = ''
    else:
        password = request.form['password']

    user = session['user']
    if not user:
        return abort(401)
    if not url:
        return abort(400)
    db_results = db.list_documents('data', 'urls', queries=[Query.equal("shortkey", shortkey)])
    if db_results['total'] == 0:
        return abort(404)
    if db_results['documents'][0]['userid'] != user:
        return abort(403)
    data = {
        'url': url,
        'shortkey': new_shortkey,
        "domain": request.form['domain']
    }
    if password: data['password'] = ph.hash(password)
    else: data['password'] = None
    db.update_document('data', 'urls', db_results['documents'][0]['$id'], data)
    all_analytics = get_all_docs('data', 'analytics', queries=[Query.equal("shortkey", shortkey)])
    for analytic in all_analytics:
        db.update_document('data', 'analytics', analytic['$id'], {
            'shortkey': new_shortkey,
        })
    print(new_shortkey)
    return redirect('/dashboard/'+new_shortkey)

@app.route("/delete", methods=['POST'])
def delete():
    shortkey = request.form['shortkey']
    user = session['user']
    if not user:
        return abort(401)
    db_results = db.list_documents('data', 'urls', queries=[Query.equal("shortkey", shortkey)])
    if db_results['total'] == 0:
        return abort(404)
    if db_results['documents'][0]['userid'] != user:
        return abort(403)
    db.delete_document('data', 'urls', db_results['documents'][0]['$id'])
    analytics = get_all_docs('data', 'analytics', queries=[Query.equal("shortkey", shortkey)])
    for analytic in analytics:
        db.delete_document('data', 'analytics', analytic['$id'])
    return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "GET": return render_template('login.html')
    username = request.form['username']
    password = request.form['password']
    if not username or not password:
        return abort(400)
    allusers = users.list(queries=[Query.equal('name', username)])['users']
    if len(allusers) == 0:
        return abort(404)
    user = allusers[0]
    if ph.verify(user['password'], password):
        session['user'] = user['$id']
        return redirect('/')
    else: return abort(403)
    
@app.route('/logout')
def logout():
    session['user'] = None
    return redirect('/')

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == "GET": return render_template('signup.html')
    username = request.form['username']
    password = request.form['password']
    if not username or not password:
        return abort(400)
    try:
        allusers = users.list(queries=[Query.equal('name', username)])['users']
        if len(allusers) > 0:
            return abort(409)
        session['user'] = users.create('unique()', name=username, password=password)['$id']
    except Exception as e:
        print(e)
        return abort(409)
    return redirect('/')

@app.route('/dashboard/<shortkey>')
def dashboard(shortkey):
    data = {
        "referrer": {},
        "browser": {},
        "os": {},
        "device": {},
        "city": {},
        "state": {},
        "country": {},
        "times": {}
    }
    db_results = get_all_docs('data', 'analytics', queries=[Query.equal("shortkey", shortkey)])
    countryicons = {}
    for visit in db_results:
        visit['time'] = datetime.datetime.date(datetime.datetime.strptime(visit['time'], '%Y-%m-%dT%H:%M:%S.000+00:00'))
        if visit['referrer'] not in data['referrer']: data['referrer'][visit['referrer']] = 0
        if visit['browser'] not in data['browser']: data['browser'][visit['browser']] = 0
        if visit['os'] not in data['os']: data['os'][visit['os']] = 0
        if visit['device'] not in data['device']: data['device'][visit['device']] = 0
        if f"{visit['city']}, {visit['state']}, {visit['country']}" not in data['city']: data['city'][f"{visit['city']}, {visit['state']}, {visit['country']}"] = 0
        if f"{visit['state']}, {visit['country']}" not in data['state']: data['state'][f"{visit['state']}, {visit['country']}"] = 0
        if visit['country'] not in data['country']: data['country'][visit['country']] = 0
        if visit['time'] not in data['times']: data['times'][visit['time']] = 0

        data['referrer'][visit['referrer']] += 1
        data['browser'][visit['browser']] += 1
        data['os'][visit['os']] += 1
        data['device'][visit['device']] += 1
        data['city'][f"{visit['city']}, {visit['state']}, {visit['country']}"] += 1
        data['state'][f"{visit['state']}, {visit['country']}"] += 1
        data['country'][visit['country']] += 1
        data['times'][visit['time']] += 1

    data['times'] = dict(sorted(data['times'].items()))
    datatimes = data['times'].copy()
    for key in data['times']:
        datatimes[key] = data['times'][key]
        if key + datetime.timedelta(days=1) not in data['times'] and key != datetime.datetime.date(datetime.datetime.now()):
            datatimes[key + datetime.timedelta(days=1)] = 0
    data['times'] = datatimes
    while True:
        if datetime.datetime.date(datetime.datetime.now()) in data['times']: break
        if data['times'] != {}:
            data['times'][list(data['times'].keys())[-1] + datetime.timedelta(days=1)] = 0
        else:
            data['times'][datetime.datetime.date(datetime.datetime.now())] = 0
            break

    data['times'] = dict(sorted(data['times'].items()))
    data['time_values'] = str(list(data['times'].values()))
    data['time_keys'] = list(data['times'].keys())
    data['time_keys'] = [str(i) for i in data['time_keys']]
    data['clicks'] = len(db_results)
    print(data)

    iconmap = {
        "Edge": "<i class='fa-brands fa-edge'></i>",
        "Chrome": "<i class='fa-brands fa-chrome'></i>",
        "Safari": "<i class='fa-brands fa-safari'></i>",
        "IE": "<i class='fa-brands fa-internet-explorer'></i>",
        "Opera": "<i class='fa-brands fa-opera'></i>",
        "Firefox": "<i class='fa-brands fa-firefox'></i>",
        "Vivaldi": "",
        "iOS": "<i class='fa-brands fa-apple'></i>",
        "Android": "<i class='fa-brands fa-android'></i>",
        "Windows": "<i class='fa-brands fa-windows'></i>",
        "Mac OS X": "<i class='fa-brands fa-apple'></i>",
        "Linux": "<i class='fa-brands fa-linux'></i>",
        "Chrome OS": "<i class='fa-brands fa-chrome'></i>",
        "Samsung": "",
    }

    return render_template('dashboard.html', data=data, iconmap=iconmap, slug=shortkey, url=db.list_documents('data', 'urls', queries=[Query.equal("shortkey", shortkey)])['documents'][0]['url'], domain=db.list_documents('data', 'urls', queries=[Query.equal("shortkey", shortkey)])['documents'][0]['domain'])

@app.route('/<shortkey>')
def redirect_to_url(shortkey):
    db_results = db.list_documents('data', 'urls', queries=[Query.equal("shortkey", shortkey)])
    if db_results['total'] == 0:
        return abort(404)

    data = db_results['documents'][0]
    url = db_results['documents'][0]['url']

    time_visited = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000+00:00")
    referrer = request.referrer
    user_agent = parse(request.headers.get('User-Agent'))
    browser = user_agent.browser.family
    os = user_agent.os.family
    device = user_agent.device.family
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    if ip == "127.0.0.1": ip = "72.23.220.139"
    print(ip)
    r = requests.get("https://api.api-ninjas.com/v1/iplookup?address="+ip, headers={"Origin": "https://api-ninjas.com", "Referer": "https://api-ninjas.com/"})

    if "country" not in r.json():
        country = "Unknown"
        state = "Unknown"
        city = "Unknown"
    else:
        country = r.json()['country']
        state = r.json()['region']
        city = r.json()['city']
    
    if data['password']:
        return render_template("password.html", data={
        "shortkey": shortkey,
        "time": time_visited,
        "referrer": referrer,
        "browser": browser,
        "os": os,
        "device": device,
        "city": city,
        "state": state,
        "country": country,
    })

    db.create_document('data', 'analytics', "unique()", {
        "shortkey": shortkey,
        "time": time_visited,
        "referrer": referrer,
        "browser": browser,
        "os": os,
        "device": device,
        "city": city,
        "state": state,
        "country": country,
    })
    return redirect(url)

@app.route('/<shortkey>/password', methods=['POST'])
def password(shortkey):
    form = request.form
    password = form['password']
    db_results = db.list_documents('data', 'urls', queries=[Query.equal("shortkey", shortkey)])
    if db_results['total'] == 0:
        return abort(404)
    if not ph.verify(db_results['documents'][0]['password'], password):
        return abort(403)

    url = db_results['documents'][0]['url']

    db.create_document('data', 'analytics', "unique()", {
        "shortkey": shortkey,
        "time": form['time'],
        "referrer": form['referrer'],
        "browser": form['browser'],
        "os": form['os'],
        "device": form['device'],
        "city": form['city'],
        "state": form['state'],
        "country": form['country'],  
    })

    return redirect(url)
    

app.run(host='0.0.0.0', port=24245)