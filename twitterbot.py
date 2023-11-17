import tweepy
import time
import emoji
import requests
import shutil
import mysql.connector
from bs4 import BeautifulSoup
from random import randint

#This script generates tweets from the content in the eBird.org website. It has two ways to do so: extracting data from a database previously created with information
#about random birds or creating a connection to the webpage eBird.org and generate it instantly. From the webpage we get concrete data that will be formatted to fit the
#character restrictions of Twitter and to give the tweet a better look with emojis and proper spacing and distribution of the information.
#If you use this code don't forget to mention me (@JVinuelas19).
#Functions:
# 1 - Generate tweets from a database (contains easter eggs)
# 2 - Generate tweets via webscrapping and saves the info into a database (if eBird is not available for data we can save the day with this database)
# 3 - Retweets other tweets related to the theme of the bot (eBird, National Geographic, etc...)
# 4 - Implement a reply system that can return a concrete bird page if asked
# 5 - Can reply 
############ TO-DO LIST:
#Ban system
#Thread generator with bird info
#Generate more engage by RTing other divulgation accounts
#Expand the birds with some pokemon birds stuff -> Maybe generate a paralel DB?



###############################################################   AUTHENTICATION FUNCTIONS   ##################################################################################

#Authentication strings used by Twitter: 
with open('texts/keys.txt') as keys:
    consumer_key = (keys.readline().strip())
    consumer_secret = (keys.readline().strip())
    access_token = (keys.readline().strip())
    access_token_secret = (keys.readline().strip())

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.Client(consumer_key=consumer_key, 
                    consumer_secret=consumer_secret, 
                    access_token=access_token, 
                    access_token_secret=access_token_secret,
                    wait_on_rate_limit=True)
media = tweepy.API(auth, wait_on_rate_limit=True)
#Starts the connection with the database:
with open('texts/dbkeys.txt') as dbkeys:
    host=dbkeys.readline().strip()
    user=dbkeys.readline().strip()
    password=dbkeys.readline().strip()
    database=dbkeys.readline().strip()
mydb = mysql.connector.connect(host=host, 
                               user=user, 
                               password=password, 
                               database=database)
mycursor = mydb.cursor()

######################################################################   WEBSCRAPPING FUNCTIONS   ############################################################################

#Saves image to file system
def save_image(image):
    r = requests.get(image, stream = True)
    if(r.status_code == 200):
        r.raw.decode_content = True
        with open ("imagenes/download.jpg", 'wb') as f:
            shutil.copyfileobj(r.raw, f)


#Saves info to database
def save_to_database(bn, sn, desc, lnk, imag):
    sql="INSERT INTO birds (name, sc_name, description, link, img) VALUES (%s, %s, %s, %s, %s)"
    data=[]
    data.append(bn)
    data.append(sn)
    data.append(desc)
    data.append(lnk)
    data.append(imag)
    mycursor.execute(sql, data)
    mydb.commit()

#Loads the bird data, saves it to db and returns it as a list
def load_data(soup, page, image, user):
    OTHER_CHARS_LEN = 8
    MAX_DATA_LEN = 280
    birdname = soup.find('span', class_='Heading-main Media--hero-title').text
    birdkey = soup.find('span', class_='Heading-sub Heading-sub--sci Heading-sub--custom u-text-4-loose').text
    details = soup.find('p', class_='u-stack-sm').text
    link = page.url
    #We fit the length of the information to the maximum space available searching the last available dot and trimming the data.
    if user is None:
        longitud = len(birdname+birdkey+link) + OTHER_CHARS_LEN
    else:
        longitud = len(birdname+birdkey+link+user) + OTHER_CHARS_LEN 

    details_max = MAX_DATA_LEN - longitud
    data = details[0:details_max]
    maxdata = data.rfind('.')
    #In case info can't fit the available length we send None values to deny the tweet, otherwise we send the tweet info to format it properly
    if maxdata > details_max:
        print("Text overflows tweet length.")
        return [None, None, None, None]
    else:
        final_data = data[0:maxdata]
        if user is None:
            save_to_database(birdname, birdkey, final_data, link, image)
        return [birdname, birdkey, final_data, link]


#Generates a string which will be the text of a tweet with the info received at the params
def gen_tweet(birdname, birdkey, final_data, link, user):
    if user is None:
        return (emoji.emojize(':bird: ') +birdname+"\n"+emoji.emojize(':woman_scientist: ') +birdkey+"\n"+emoji.emojize(':information: ') +final_data+'.'+"\n"
        +emoji.emojize(':magnifying_glass_tilted_right: ')+link)    
    else:
        return (user+'\n'+emoji.emojize(':bird: ') +birdname+"\n"+emoji.emojize(':woman_scientist: ') +birdkey+"\n"+emoji.emojize(':information: ') +final_data+'.'+"\n"
        +emoji.emojize(':magnifying_glass_tilted_right: ')+link)    


#Requests a random bird to eBird.org or to the species code contained in the link argument
def request_bird(link, user):
    image_found = False
    petition = False
    #Sometimes the bird has no images. In order to avoid it this loop makes a new try every time the webpage has no images attached.
    while(image_found is False):
        if (link is None):
            url = 'https://ebird.org/species/surprise-me'
        else:
            url = f'https://ebird.org/species/{link}'
            petition = True
            print(f'El enlace solicitado es {url}')
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        imgTag = soup.find('img')
        try:
            image = imgTag['src']
            image_found = True
            save_image(image)
            return load_data(soup, page, image, user)
        except:
            if petition is True:
                break
            else:
                if image_found is False:
                    print('Image not found. Trying again...')
                else:
                    print("Something happened in the data management")
            

#Function that searches the bird in yahoo and obtains the link to the eBird page. With the link we call the webscrapper function and get the bird
def pick_a_bird(bird):
    url = f"https://es.search.yahoo.com/search?p={bird} eBird"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    species = soup.find('span', class_='fc-pewter').text
    species_list = species.split()
    species_code = species_list[3]
    return species_code

#####################################################################   TWEETING FUNCTIONS   ################################################################################

#Reads the last tweet id registered
def read_tweet_id(id_type):
    with open('texts/last_id.txt', 'r') as file:
        lines = file.readlines()
        id = int(lines[id_type]) 
    return id


#Writes the last tweet id registered
def store_tweet_id(id_number, id_type):
    with open('texts/last_id.txt', 'r+') as file:
        lines = file.read().splitlines()
        file.seek(0)
        file.truncate(0)
        lines[id_type] = str(id_number)
        for line in lines:
            file.write(f"{line}\n")
    

#Creates a tweet from the database. It generates a random number between 0 and 100. If it's not 50, generates a second random number between 1 and the database length.
#If it is 50 it generates a funny tweet.
def tweetbird_db():
    gen1 = randint(0,100)
    if gen1 != 50:
        #Gets the bird info from the database based on gen2
        mycursor.execute("SELECT COUNT(*) FROM birds")
        longitud = mycursor.fetchone()
        gen2 = randint(1,longitud[0])
        query=f"SELECT name, sc_name, description, link, img FROM birds WHERE id={str(gen2)}"
        mycursor.execute(query)
        result = mycursor.fetchone()
        birdname=result[0]
        birdkey=result[1]
        description=result[2]
        link=result[3]
        img=result[4]
        birdtweet = (emoji.emojize(':bird: ') + birdname +"\n"+emoji.emojize(':woman_scientist: ') +birdkey+"\n"+emoji.emojize(':information: ') +description+'.'+"\n"
        +emoji.emojize(':magnifying_glass_tilted_right: ')+link)

        #Obtains the image and saves it to a rewritable file. File is overwritten each time this function is used to avoid generating too much images.
        r = requests.get(img, stream = True)
        if(r.status_code == 200):
            r.raw.decode_content = True
            with open ("imagenes/download.jpg", 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        
        #Creates the tweet with all the information obtained and tweets it
        image = media.media_upload("imagenes/download.jpg")
        api.create_tweet(text=birdtweet, media_ids=[image.media_id], user_auth=True)
    #Funny tweet
    else:   
        anivia(None, 0)


#Creates a tweet straight from the eBird web. This function occurs in the webscrapper.py file
def tweetbird_scrap():
    data=request_bird(None, None)
    #try:
    birdtweet=gen_tweet(data[0],data[1],data[2],data[3], None)
    image = media.media_upload("imagenes/download.jpg")
    api.create_tweet(text=birdtweet, media_ids=[image.media_id])
#except:
     #   print("Unable to format bird data. Tweet is longer than available.")


#Check the mentions generated by users that mention @Ornithob0t. If the user requests a bird using the keyphrase "Talk me about the <birdname>", the function will scrap
#data about that bird and respond with some info about it.
def check_mentions():
    getBlocked = False
    MAX_BADWORDS = 253
    i = 0
    mentions = api.mentions_timeline(tweet_mode = 'extended')
    if(mentions[0].id > read_tweet_id(1)):
        for tweet in reversed(mentions):
            if(tweet.id > read_tweet_id(1)):
                txt = tweet.full_text
                casefold_tweet = txt.casefold()
                #if "talk me about" in casefold_tweet:
                if casefold_tweet.startswith("@ornithob0t talk me about the "):
                    user = f"@{tweet.user.screen_name}"
                    cut = casefold_tweet.rpartition(" talk me about the ")
                    if cut[2] == 'anivia':
                        anivia(user, tweet.id)
                    else:
                        #print(f"Mensaje extraido del tweet target: {cut[2]}")
                        code = pick_a_bird(cut[2])
                        #print(f"El codigo es {code} y el user es {user}")
                        data=request_bird(code, user)
                        #print("El request bird ha terminado")
                        birdtweet=gen_tweet(data[0],data[1],data[2],data[3], user)
                        media = api.media_upload("imagenes/download.jpg")
                        #print('Imagen subida al server')
                        api.update_status(status=birdtweet, in_reply_to_status_id=tweet.id, auto_populate_reply_metadata=True, media_ids=[media.media_id])
                        print('Tweet enviado')
                else:
                    with open('texts/badwords.txt', 'r') as badwords:
                        word = badwords.read().splitlines()
                        while(not getBlocked and i <= MAX_BADWORDS):
                            #if (word[i].casefold() in casefold) is True):
                            if (casefold_tweet.find(word[i].casefold()) != -1):
                                print(f"He encontrado una palabrota: {word[i]}")
                                insulto=word[i]
                                getBlocked=True
                            else:
                                i+=1
                        
                        #Responder al tweet de la mención
                        #Acceder a la blacklist, revisar si el usuario está anotado (si no lo está anotarlo y salir), revisar anotaciones previas y si es 3 bloquear durante 30 dias a partir de la fecha de insulto
                        #Bloquear al menda
                        #Generar varias respuestas haters
                        if (getBlocked):
                            status=f"@{tweet.user.screen_name} como me vuelvas a llamar {insulto} te reviento la puta cara de gafas que tienes y te vas bloqueado por subnormal."
                            api.update_status(status=status, in_reply_to_status_id=tweet.id, auto_populate_reply_metadata=True)    
                i = 0
                getBlocked = False
                store_tweet_id(tweet.id, 1)
                time.sleep(5)
    else:
        print("No new mentions!")

#Funny tweet generator
def anivia(user, id):
    image = media.media_upload('imagenes/anivia.jpg')
    if(user is None and id == 0):
        tweet = emoji.emojize(':bird: ') +"Anivia\n"+emoji.emojize(':woman_scientist: ')+"The cryophoenix\n"+emoji.emojize(':information: ')+"My favorite champion with no doubt Anivia, the cryophoenix. She won't have much attack, she won't have much defense... but I love her. It's very hard to control, especially the Q.\n"+emoji.emojize(':magnifying_glass_tilted_right: ')+"https://www.leagueoflegends.com/en-gb/champions/anivia/"
        api.create_tweet(text=tweet, media_ids=[image.media_id])
    else:
        tweet = user+'\n'+emoji.emojize(':bird: ') +"Anivia\n"+emoji.emojize(':woman_scientist: ')+"The cryophoenix\n"+emoji.emojize(':information: ')+"My favorite champion with no doubt Anivia, the cryophoenix. She won't have much attack, she won't have much defense... but I love her. It's very hard to control, especially the Q.\n"+emoji.emojize(':magnifying_glass_tilted_right: ')+"https://www.leagueoflegends.com/en-gb/champions/anivia/"
        api.create_tweet(text=tweet, in_reply_to_status_id=id, auto_populate_reply_metadata=True, media_ids=[image.media_id])
        store_tweet_id(id,1)


#Reply Jesus
def lord_and_savior(user):
    id = read_tweet_id(2)
    jesus = False
    tweets = api.user_timeline(screen_name=user, include_rts=False)
    if(tweets[0].id> int(id)):
        print(f"{tweets[0].id} y {id}")
        for tweet in reversed(tweets):
            tweet_content = tweet.text.casefold()
            print(f"tweet is: {tweet_content}")
            words = ["jesus", "jesús", "@jjmarlb"]
            for word in words:
                if tweet_content.find(word) != -1:
                    jesus = True
                    break
                    
            if(tweet.id > int(id) and jesus):
                with open("texts/memes.txt", "r") as memes:
                    list_memes = memes.readlines()
                    meme = list_memes[randint(0,26)]
                status=f"@{tweet.user.screen_name} {meme}"
                api.update_status(status=status, in_reply_to_status_id=tweet.id)
                store_tweet_id(tweet.id, 2)
                jesus = False

            time.sleep(30)
    else:
        print("No Jesus memes")
        
    return 0

#Checks the eBird account and retweets everything since the last saved tweet ID. The user_timeline() function returns the last 20 tweets from the account.
#We store that number to perform with the algorithm to retweet the most recent tweets
def retweet():
    #Gets the last retweet from file and try to search more tweets after the stored one. 
    id = read_tweet_id(0)
    tweets = api.get_users_tweets(id="Team_eBird")    
    #If there are new tweets, the bot will retweet and sleep some seconds to avoid spam. Once the list is over saves the last retweet ID and end.
    if(tweets[0].id>id):
        for tweet in tweets:
            if(tweet.id > id):
                id = tweet.id
                try:
                    api.retweet(tweet.id)
                    print("New retweet!")
                    time.sleep(30)
                except:
                    print("Already retweeted")


        store_tweet_id(id, 0)
        print("RTs done!")
                
    #If there are no new tweets it will print a message
    else:
        print("There are no tweets to retweet")
    

######################################################################   MAIN SECTION   ######################################################################################

def main():
    try:
        tweetbird_scrap()
    except:
        tweetbird_db()
 
if __name__ == "__main__":
    main()
