import tweepy
import schedule
import time
import webscrapper
import emoji
import requests
import shutil
import mysql.connector
from random import randint

#This script generates tweets from the content in the eBird.org website. It has two ways to do so: extracting data from a database previously created with information
#about random birds or creating a connection to the webpage eBird.org and generate it instantly. From the webpage we get concrete data that will be formatted to fit the
#character restrictions of Twitter and to give the tweet a better look with emojis and proper spacing and distribution of the information.
#If you use this code don't forget to mention me at least one time (@JVinuelas19).

#Authentication strings used by Twitter: 
with open('keys.txt') as keys:
    consumer_key = (keys.readline().strip())
    consumer_secret = (keys.readline().strip())
    access_token = (keys.readline().strip())
    access_token_secret = (keys.readline().strip())
    keys.close()

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

#Starts the connection with the database:
with open('dbkeys.txt') as dbkeys:
    host=dbkeys.readline().strip()
    user=dbkeys.readline().strip()
    password=dbkeys.readline().strip()
    database=dbkeys.readline().strip()
    dbkeys.close()
mydb = mysql.connector.connect(host=host, user=user, password=password, database=database)
mycursor = mydb.cursor()

#Reads the last tweet id registered
def read_tweet_id():
    file = open('last_id.txt', 'r')
    id = int(file.read().strip())
    file.close()
    return id

#Writes the last tweet id registered
def store_tweet_id():
    file = open('last_id.txt', 'w')
    file.write(str(id))
    file.close()

#Creates a tweet from the database. It generates a random number between 0 and 100. If it's not 50, generates a second random number between 1 and the database length.
#If it is 50 it generates a funny tweet.
def tweetbird_db():
    gen1 = randint(0,100)
    if gen1 != 50:
        #Gets the bird info from the database based on gen2
        gen2 = randint(1,1413)
        query="SELECT name, sc_name, description, link, img FROM birds WHERE id="+str(gen2)
        mycursor.execute(query)
        result = mycursor.fetchone()
        birdname=result[0]
        birdkey=result[1]
        description=result[2]
        link=result[3]
        img=result[4]
        birdtweet = (emoji.emojize(':bird: ') +birdname+"\n"+emoji.emojize(':woman_scientist: ') +birdkey+"\n"+emoji.emojize(':information: ') +description+'.'+"\n"
        +emoji.emojize(':magnifying_glass_tilted_right: ')+link)

        #Obtains the image and saves it to a rewritable file. File is overwritten each time this function is used to avoid generating too much images.
        r = requests.get(img, stream = True)
        if(r.status_code == 200):
            r.raw.decode_content = True
            with open ("imagenes/download.jpg", 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        
        #Creates the tweet with all the information obtained and tweets it
        media = api.media_upload("imagenes/download.jpg")
        api.update_status(status=birdtweet, media_ids=[media.media_id])
    #Funny tweet
    else:   
        anivia()

#Creates a tweet straight from the eBird web. This function occurs in the webscrapper.py file
def tweetbird_scrap():
    birdtweet=webscrapper.main()
    media = api.media_upload("imagenes/download.jpg")
    api.update_status(status=birdtweet, media_ids=[media.media_id])

#Check the mentions generated by users that mention @Ornithob0t. Has no function yet, will be added to generate interactivity soon.
def check_mentions():
    mentions = api.mentions_timeline(tweet_mode = 'extended')
    for tweet in reversed(mentions):
        print (tweet.full_text)

#Funny tweet generator
def anivia():
    media = api.media_upload('imagenes/anivia.jpg')
    tweet = emoji.emojize(':bird: ') +"Anivia\n"+emoji.emojize(':woman_scientist: ')+"The cryophoenix\n"+emoji.emojize(':information: ')+"My favorite champion with no doubt Anivia, the cryophoenix. She won't have much attack, she won't have much defense... but I love her. It's very hard to control, especially the Q.\n"+emoji.emojize(':magnifying_glass_tilted_right: ')+"https://www.leagueoflegends.com/en-gb/champions/anivia/"
    api.update_status(status=tweet, media_ids=[media.media_id])

#Main loop
def main():
    #Schedules 2 tweets at 2 different times everyday. Currently calls tweetbird_scrap() straight because i have no servers to keep the bot working all the time.
    #Don't use the tweet functions in the next while loop. Otherwise the bot will be tweeting each thirty seconds, and you can disturb Elon Musk and get the account suspended.
    tweetbird_scrap()
    schedule.every().day.at("10:00:00").do(tweetbird_scrap)
    schedule.every().day.at("20:00:00").do(tweetbird_scrap)
    while True:
        #Check pending schedules, execute them if exists and sleeps for (in my case) 30 seconds.
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()
