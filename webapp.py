from flask import Flask, redirect, url_for, session, request, jsonify, render_template, flash
from markupsafe import Markup
from flask_oauthlib.client import OAuth
from bson.objectid import ObjectId

import pprint
import os
import time
import pymongo
import sys
import copy
import random
 
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

# Generated by Perplexity so I don't have to write all of them out :D
deck = [
    # Hearts
    "AH", "2H", "3H", "4H", "5H", "6H", "7H", "8H", "9H", "10H", "JH", "QH", "KH",
    
    # Diamonds
    "AD", "2D", "3D", "4D", "5D", "6D", "7D", "8D", "9D", "10D", "JD", "QD", "KD",
    
    # Clubs
    "AC", "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "10C", "JC", "QC", "KC",
    
    # Spades
    "AS", "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S", "10S", "JS", "QS", "KS"
]

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
    return render_template('profile.html', profilePhoto=session['user_data']["avatar_url"], username=session['user_data']["login"])

@app.route('/shop')
def renderShop():
    coins = getCoins()
    if 'github_token' not in session:
        return redirect('/login')
    return render_template('shop.html')
    
@app.route('/play',methods=['GET','POST'])
def renderPlay():
    game = None

    revealed = True
    # These cookies store the bot and player hands, however they may not be necessary since the player is not ever actually playing a card
    # if "bot_hand" not in session:
        # session["bot_hand"] = []
    # if "player_hand" not in session:
        # session["player_hand"] = []
    
    if "playing" not in session:
        session["playing"] = True
    
    for i in games.find({'uid':session['user_data']['id']}):
        game = i
    
    if game:
        playing = session["playing"]
        player_cards = game["player_hand"]
        bot_cards = game["bot_hand"]

        
        # session["player_hand"] = player_cards
        # session["bot_hand"] = bot_cards
        # Set revealed to True when the player stands, this will reveal the bot's second card
        
        if getHandValue(player_cards) >= 21:
            playing = False
            session["playing"] = playing
        
        if playing:
            revealed=False

        return render_template('play.html', player_hand=player_cards, bot_hand=bot_cards, revealed=revealed, playing=playing)
    else:
        startGame()
        return redirect('/play')

@app.route('/stop_playing')
def stopPlaying():
    # placeholder
    return redirect('/profile')


@app.route('/new_game')
def newGame():
    # TODO: Add a check for whether the player's game is done, and keep them on the same game if they press the button but aren't done, since if they could press the button
    # and start a new game, without being done with their current one, they could just start a ton of new games until they start with a really good hand
    # if done:
    games.delete_one({'uid':session['user_data']['id']})
    return redirect('/play')


# Intending to use AJAX later to prevent the entire webpage from reloading for the user every time they choose hit or stand
@app.route('/action', methods=['POST'])
def action():
    playing = session["playing"]
    new_cards = None
    
    
    for i in games.find({'uid':session['user_data']['id']}):
        game = i
    
    if game:
        player_cards = game["player_hand"]
        bot_cards = game["bot_hand"]

        userAction = request.form.get("action")
        
        new_cards, isPlaying = playerAction(userAction,player_cards,bot_cards)
        if isPlaying == -1:
            isPlaying = False
            busted = True
        playing = isPlaying
        session["playing"] = isPlaying
        print(isPlaying)
        updatePlayerHand(new_cards)
        
    else:
        startGame()
        return redirect('/play')
    
    
    if not playing:
        revealed = True
        # bot_cards, gameOver = botAction(player_cards, bot_cards)
        # updateBotHand(game, bot_cards)
        
        
    else:
        # player_cards, gameOver = playerAction(userAction, player_cards, bot_cards)
        
        revealed=False
    
    
    return render_template('play.html', player_hand=new_cards, bot_hand=bot_cards, revealed=revealed, playing=playing)

@app.route('/buy',methods=['POST'])
def buyItem():
    if getCoins() >= int(request.form["itemValue"]):
        addCoins(int(request.form["itemValue"]))
        print("Bought "+request.form["boughtItemId"]+" Successfully!")
    else:
        print("Not enough coins to buy "+request.form["boughtItemId"]+"!")
    return redirect('/shop',code=302)


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
    newGame = {"uid": session['user_data']['id'], "bot_hand": botHand, "player_hand": playerHand}
    games.insert_one(newGame)
    session["playing"] = True



def getCards(numCards, usedCards):
    cards = []
    newDeck = copy.deepcopy(deck) # Making a deep copy to manipulate to prevent the deck List from changing
    random.shuffle(newDeck)
    
    if usedCards is not None:
        for i in usedCards:
            newDeck.remove(i)
    
    if numCards > len(newDeck):
        return newDeck
    
    for i in range(numCards):
        rand = random.randint(0, len(newDeck) - 1)
        card = newDeck[rand]
        cards.append(card)
        newDeck.remove(card)
        
    
    return cards


# Updates the player's hand on MongoDB
def updatePlayerHand(hand):
    changes = {'$set':{"player_hand": hand}}
    query = {"uid":session["user_data"]["id"]}
    
    # print(query)
    # print(games.find_one(query))
    games.update_one(query, changes)
    return True


# Updates the bot's hand on MongoDB
def updateBotHand(hand):
    changes = {'$set':{"bot_hand": hand}}
    query = {"uid":session["user_data"]["id"]}
    games.update_one(query, changes)




# Returns the next game state when the player takes a given action (either hit or stand, for now -- will probably add double and split options later)
# Returns -1 if player has busted, or returns the player's new hand if not along with a boolean for whether or not the bot should take its action
#Returns 0 if the player takes no action
def playerAction(action, playerHand, botHand):
    print(action)
    if action == "hit":
        playerHand += getCards(1, playerHand + botHand)
        value = getHandValue(playerHand)
        if value == 21:
            return playerHand, False
        elif value > 21:
            return playerHand,-1
        else:
            return playerHand, True
    
    if action == "stand":
        value = getHandValue(playerHand)
        return playerHand, False
    return 0,0
    
# Returns 
# def botAction(playerHand, botHand):
    
    
    
    

# Gets the value of a single card, returns 11 by default for an ace and 10 for face cards
def getCardValue(card):
    value = card[0]
    
    if value == 'A':
        return 11
    if value == 'K':
        return 10
    if value == 'Q':
        return 10
    if value == 'J':
        return 10
    if value == 'T':
        return 10
    
    return int(value)
    
    

# Gets the value of a given hand of cards, uses 1 or 11 for an ace depending on the value of the rest of the hand, with 11 as default
def getHandValue(hand):
    value = 0
    aces = []
    
    for card in hand:
        if card[0] != 'A':
            value += getCardValue(card)
        else:
            aces.append(card)
    
    for ace in aces:
        if value + 11 > 21:
            value += 1
        else:
            value += 11
    
    
    return value



if __name__ == '__main__':
    app.run()
