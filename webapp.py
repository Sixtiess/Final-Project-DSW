from flask import Flask, redirect, url_for, session, request, jsonify, render_template, flash
from markupsafe import Markup
from flask_oauthlib.client import OAuth
from bson.objectid import ObjectId

import pprint
import os
import time
import pymongo
import sys
 
app = Flask(__name__)

app.debug = True #Change this to False for production
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' #Remove once done debugging

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)
oauth.init_app(app) #initialize the app to be able to make requests for user information

#Set up GitHub as OAuth provider
github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], #your web app's "username" for github's OAuth
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],#your web app's "password" for github's OAuth
    request_token_params={'scope': 'user:email'}, #request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',  
    authorize_url='https://github.com/login/oauth/authorize' #URL for github's OAuth login
)

#Connect to database
url = os.environ["MONGO_CONNECTION_STRING"]
client = pymongo.MongoClient(url)
db = client[os.environ["MONGO_DBNAME"]]
users = db['Users']
games = db['Games']

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

#context processors run before templates are rendered and add variable(s) to the template's context
#context processors must return a dictionary 
#this context processor adds the variable logged_in to the conext for all templates
@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/')
def home():
    if 'github_token' in session:
        return redirect('/profile')
    return render_template('login.html')

#redirect to GitHub's OAuth page and confirm callback URL
@app.route('/login')
def login():
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='http')) #callback URL must match the pre-configured callback URL

@app.route('/logout')
def logout():
    session.clear()
    flash('You were logged out.')
    return redirect('/')

@app.route('/login/authorized')
def authorized():
    
    
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        flash('Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args), 'error')      
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            message = 'You were successfully logged in as ' + session['user_data']['login'] + '.'
            
            # Checking if the user exists or if they are a new user, and adding them to the database if they are
            ids = []
            for user in users.find():
                ids.append(user['uid'])
            
            if not session['user_data']['id'] in ids:
                name = session['user_data']['login']
                new_user = {
                    'name': name, 
                    'coins': 0, 
                    'uid': session['user_data']['id']
                }
                users.insert_one(new_user)
                print("Added new user " + name + " to database")
                
        except Exception as inst:
            session.clear()
            print(inst)
            message = 'Unable to login, please try again.', 'error'
            return redirect('/')
    return redirect('/profile')


@app.route('/profile')
def renderProfile():
    if 'github_token' not in session:
        return redirect('/login')
    return render_template('profile.html')

@app.route('/shop')
def renderShop():
    coins = getCoins()
    if 'github_token' not in session:
        return redirect('/login')
    return render_template('shop.html')
    
@app.route('/play')
def renderPlay():
    game = None
    for i in games.find({'playerid':session['user_data']['id']}):
        game = i
    
    if game:
        player_cards = game["player_hand"]
        return render_template('play.html', player_hand=player_cards)
    else:
        startGame()
        redirect('/play')

#the tokengetter is automatically called to check who is logged in.
@github.tokengetter
def get_github_oauth_token():
    return session['github_token']


def getCoins():
    if 'github_token' not in session:
        session['coins'] = 0
        return 0
    
    if 'coins' not in session:
        session['coins'] = -1
    
    for i in users.find({'uid':session['user_data']['id']}):
        user = i
    
    
    try:
        session['coins'] = user['coins']
        return user['coins']
    except:
        session['coins'] = 0
        return 0
   
   
def addCoins(amount):
    if 'github_token' not in session:
        return False
    
    if 'coins' not in session:
        return False
    
    for i in users.find({'uid':session['user_data']['id']}):
        user = i
    
    
    try:
        newAmount = session['coins'] + amount;
        query = {'uid':session['user_data']['id']}
        changes = {'$set': {'coins': newAmount}}
        users.update_one(query, changes)
        return True
    except:
        return False


def setCoins(amount):
    if 'github_token' not in session:
        return False
    
    if 'coins' not in session:
        return False
    
    for i in users.find({'uid':session['user_data']['id']}):
        user = i
    
    
    try:
        query = {'uid':session['user_data']['id']}
        changes = {'$set': {'coins': amount}}
        users.update_one(query, changes)
        return True
    except:
        return False



def startGame():
    botHand = getCards(2, None)
    playerHand = getCards(2, botHand)
    newGame = {"playerid": session['user_data']['id'], "bot_hand": botHand, "player_hand": player_hand}
    games.insert_one(newGame)

if __name__ == '__main__':
    app.run()
