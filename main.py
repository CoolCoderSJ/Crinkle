from flask import Flask, render_template, request, redirect, session, abort, flash
from flask_session import Session
import random, string, datetime, requests, os, json
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
    domains = get_all_docs('domains', 'domains', queries=[Query.equal("userid", user)])
    return render_template('index.html', links=links, domains=domains)

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
    domain = request.form['domain']
    user = session['user']
    if not user:
        return abort(401)
    if not url:
        pass
        # return abort(400)
    if domain != "url.shuchir.dev" and domain != "localhost":  
        db_dom = db.list_documents('domains', 'domains', queries=[Query.equal("domain", domain)])
        if db_dom['total'] == 0:
            flash("Domain does not exist. Add it through Settings.")
            return redirect('/')
        if db_dom['documents'][0]['userid'] != user:
            flash("You do not own this domain. Verify ownership through settings")
            return redirect('/')
        if "/" in domain or "\\" in domain:
            flash("unsafe character in domain")
            return redirect('/')

    db_results = db.list_documents('data', 'urls', queries=[Query.equal("shortkey", shortkey), Query.equal("domain", domain)])
    if db_results['total'] > 0:
        flash("The slug you used already exists")
        return redirect('/')
    data = {
        'url': url,
        'shortkey': shortkey,
        'userid': user,
        "domain": domain
    }
    if password: data['password'] = ph.hash(password)
    db.create_document('data', 'urls', "unique()", data)
    return redirect('/dashboard/'+domain+"/"+shortkey)

@app.route("/edit", methods=['POST'])
def edit():
    url = request.form['url']
    shortkey = request.form['old_shortkey']
    old_domain = request.form['old_domain']

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
    db_results = db.list_documents('data', 'urls', queries=[Query.equal("shortkey", shortkey), Query.equal("domain", old_domain)])
    if db_results['total'] == 0:
        return abort(404)
    if db_results['documents'][0]['userid'] != user:
        return abort(403)

    domain = request.form['domain']
    if domain != "url.shuchir.dev" and domain != "localhost": 
        db_dom = db.list_documents('domains', 'domains', queries=[Query.equal("domain", domain)])
        if db_dom['total'] == 0:
            flash("Domain does not exist. Add it through Settings.")
            return redirect('/dashboard/'+old_domain+"/"+shortkey)
        if db_dom['documents'][0]['userid'] != user:
            flash("You do not own this domain. Verify ownership through settings")
            return redirect('/dashboard/'+old_domain+"/"+shortkey)
        if "/" in domain or "\\" in domain:
            flash("unsafe character in domain")
            return redirect('/dashboard/'+old_domain+"/"+shortkey)

        
    data = {
        'url': url,
        'shortkey': new_shortkey,
        "domain": domain
    }
    if password: data['password'] = ph.hash(password)
    else: data['password'] = None
    db.update_document('data', 'urls', db_results['documents'][0]['$id'], data)
    all_analytics = get_all_docs('data', 'analytics', queries=[Query.equal("shortkey", shortkey), Query.equal("domain", old_domain)])
    for analytic in all_analytics:
        db.update_document('data', 'analytics', analytic['$id'], {
            'shortkey': new_shortkey,
            "domain": domain
        })
    print(new_shortkey)
    return redirect('/dashboard/'+domain+"/"+new_shortkey)

@app.route("/delete", methods=['POST'])
def delete():
    shortkey = request.form['shortkey']
    domain = request.form['domain']
    user = session['user']
    if not user:
        return abort(401)
    db_results = db.list_documents('data', 'urls', queries=[Query.equal("shortkey", shortkey), Query.equal("domain", domain)])
    if db_results['total'] == 0:
        return abort(404)
    if db_results['documents'][0]['userid'] != user:
        return abort(403)
    db.delete_document('data', 'urls', db_results['documents'][0]['$id'])
    analytics = get_all_docs('data', 'analytics', queries=[Query.equal("shortkey", shortkey), Query.equal("domain", domain)])
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
        flash("User does not exist")
        return redirect("/login")
    user = allusers[0]
    try:
        ph.verify(user['password'], password)
        session['user'] = user['$id']
        return redirect('/')
    except: 
        flash("Incorrect password")
        return redirect("/login")
    
@app.route('/logout')
def logout():
    session['user'] = None
    return redirect('/')

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == "GET": return render_template('signup.html')
    username = request.form['username']
    password = request.form['password']
    if len(password) < 8: 
        flash("Password must be at least 8 characters long")
        return redirect("/signup")
    if not username or not password:
        return abort(400)
    try:
        allusers = users.list(queries=[Query.equal('name', username)])['users']
        if len(allusers) > 0:
            flash("User already exists")
            return redirect("/signup")
        session['user'] = users.create('unique()', name=username, password=password)['$id']
    except Exception as e:
        print(e)
        return abort(409)
    return redirect('/')

@app.route('/dashboard/<domain>/<shortkey>')
def dashboard(domain, shortkey):
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
    db_results = get_all_docs('data', 'analytics', queries=[Query.equal("shortkey", shortkey), Query.equal("domain", domain)])
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
    return render_template('dashboard.html', data=data, iconmap=iconmap, 
                            slug=shortkey, url=db.list_documents('data', 'urls', queries=[Query.equal("shortkey", shortkey), Query.equal("domain", domain)])['documents'][0]['url'], 
                            domain=domain,
                            username=users.get(session['user'])['name'])

@app.route("/settings")
def settings():
    if "user" not in session:
        return redirect('/')
    if not session['user']: 
        return redirect('/')
    unverified_domains = get_all_docs('domains', 'verificationCodes', queries=[Query.equal("userid", session['user'])])
    verified_domains = get_all_docs('domains', 'domains', queries=[Query.equal("userid", session['user'])])
    username = users.get(session['user'])['name']
    return render_template("settings.html", unverified_domains=unverified_domains, verified_domains=verified_domains, username=username)

@app.route("/user/update/username", methods=['POST'])
def update_user():
    new_username = request.form['username']
    if not new_username:
        return abort(400)
    allusers = users.list(queries=[Query.equal('name', new_username)])['users']
    if len(allusers) > 0:
        flash("User already exists")
        return redirect("/settings")
    users.update_name(session['user'], new_username)
    session['user'] = users.get(session['user'])['$id']
    flash("Username updated")
    return redirect("/settings")

@app.route("/user/update/password", methods=['POST'])
def update_password():
    old_password = request.form['old_password']
    new_password = request.form['new_password']
    if  not old_password or not new_password:
        return abort(400)
    user = users.get(session['user'])
    try:
        ph.verify(user['password'], old_password)
    except: 
        flash("Incorrect password")
        return redirect("/settings")

    if len(new_password) < 8:
        flash("Password must be at least 8 characters long")
        return redirect("/settings")
    users.update_password(session['user'], new_password)
    flash("Password updated")
    return redirect("/settings")

@app.route("/domain/add", methods=['POST'])
def add_domain():
    domain = request.form['domain']
    if not domain:
        return abort(400)
    if "/" in domain or "\\" in domain:
        flash("unsafe character in domain")
        return redirect('/settings')
    db_results = db.list_documents('domains', 'domains', queries=[Query.equal("domain", domain)])
    if db_results['total'] > 0:
        flash("Domain already exists")
        return redirect('/settings')
    db_results = db.list_documents('domains', 'verificationCodes', queries=[Query.equal("domain", domain)])
    if db_results['total'] > 0:
        flash("Domain already exists")
        return redirect('/settings')
    
    db.create_document('domains', 'verificationCodes', "unique()", {
        "domain": domain,
        "userid": session['user'],
        "code": ''.join(random.choice(string.ascii_letters) for i in range(10))
    })
    flash("Domain added. Verify ownership through DNS records.")
    return redirect('/settings')

@app.route("/domain/delete/<collection>", methods=['POST'])
def delete_domain(collection):
    domain = request.form['domain']
    if not domain:
        return abort(400)
    db_results = db.list_documents('domains', collection, queries=[Query.equal("domain", domain)])
    if db_results['total'] == 0:
        flash("Domain does not exist")
        return redirect('/settings')
    if db_results['documents'][0]['userid'] != session['user']:
        flash("You do not own this domain")
        return redirect('/settings')

    db.delete_document('domains', collection, db_results['documents'][0]['$id'])
    flash("Domain deleted")
    return redirect('/settings')

@app.route("/domain/verify", methods=['POST'])
def verify_domain():
    domain = request.form['domain']
    if not domain:
        return abort(400)
    db_results = db.list_documents('domains', 'verificationCodes', queries=[Query.equal("domain", domain)])
    if db_results['total'] == 0:
        flash("Domain does not exist")
        return redirect('/settings')
    if db_results['documents'][0]['userid'] != session['user']:
        flash("You do not own this domain")
        return redirect('/settings')

    a = requests.get("https://dns.google/resolve?name=link.industeeltech.org&type=A").json()
    A_records = []
    for ans in a['Answer']: A_records.append(ans['data'])
    if not "132.145.139.96" in A_records:
        flash("Crinkle could not find a valid A record")
        return redirect('/settings')

    txt = a = requests.get("https://dns.google/resolve?name=link.industeeltech.org&type=TXT").json()
    TXT_records = []
    for ans in txt['Answer']: TXT_records.append(ans['data'])
    print(TXT_records)
    if not "crinkle-domain-verification-" + db_results['documents'][0]['code'] in TXT_records:
        flash("Crinkle could not find a valid TXT record")
        return redirect('/settings')


    db.create_document('domains', 'domains', "unique()", {
        "domain": domain,
        "userid": session['user']
    })

    url = "https://nginx.shuchir.dev/api/tokens"
    payload = json.dumps({"identity":"shuchir.jain@gmail.com","secret":os.environ['NGINX_PASSWORD']})
    headers = {
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'authorization': 'Bearer null',
    'content-type': 'application/json; charset=UTF-8',
    'origin': 'https://nginx.shuchir.dev',
    'referer': 'https://nginx.shuchir.dev/login',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.200'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    token = response.json()['token']
    print(token)
    
    url = "https://nginx.shuchir.dev/api/nginx/proxy-hosts?expand=owner,access_list,certificate"

    payload = {}
    headers = {
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'authorization': 'Bearer '+token,
    'content-type': 'application/json; charset=UTF-8',
    'referer': 'https://nginx.shuchir.dev/nginx/proxy',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.200'
    }

    r = requests.request("GET", url, headers=headers, data=payload)
    res = next((sub for sub in r.json() if sub['id'] == 19), None)
    print(res)

    res['domain_names'].append(domain)
    print(res['domain_names'])

    url = "https://nginx.shuchir.dev/api/nginx/proxy-hosts/19"

    payload = json.dumps({"domain_names":res['domain_names'],"forward_scheme":"http","forward_host":"132.145.139.96","forward_port":24245,"allow_websocket_upgrade":True,"access_list_id":"0","certificate_id":"new","http2_support":True,"meta":{"letsencrypt_email":"shuchir.jain@gmail.com","letsencrypt_agree":True,"dns_challenge":False},"advanced_config":"","locations":[],"block_exploits":False,"caching_enabled":False,"hsts_enabled":False,"hsts_subdomains":False,"ssl_forced":False})
    headers = {
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'authorization': 'Bearer '+token,
    'content-type': 'application/json; charset=UTF-8',
    'origin': 'https://nginx.shuchir.dev',
    'referer': 'https://nginx.shuchir.dev/nginx/proxy'
    }

    response = requests.request("PUT", url, headers=headers, data=payload)
    print(response.text)
    if "error" in response.json(): flash("error"); return redirect('/settings')

    db.delete_document('domains', 'verificationCodes', db_results['documents'][0]['$id'])
    flash("Domain verified")
    return redirect('/settings')

@app.route('/<shortkey>/password', methods=['POST'])
def password(shortkey):
    o = urlparse(request.base_url)
    domain = o.hostname
    form = request.form
    password = form['password']
    db_results = db.list_documents('data', 'urls', queries=[Query.equal("shortkey", shortkey), Query.equal("domain", domain)])
    if db_results['total'] == 0:
        return render_template("404.html")
    try:
        ph.verify(db_results['documents'][0]['password'], password)
    except:
        flash("Incorrect password")
        return redirect('/'+shortkey)

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
        "domain": domain
    })

    return redirect(url)


@app.route('/<shortkey>')
def redirect_to_url(shortkey):
    o = urlparse(request.base_url)
    domain = o.hostname
    db_results = db.list_documents('data', 'urls', queries=[Query.equal("shortkey", shortkey), Query.equal("domain", domain)])
    if db_results['total'] == 0:
        return render_template("404.html")

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
        "domain": domain
    })
    return redirect(url)

app.run(host='0.0.0.0', port=24245, debug=True)