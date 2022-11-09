from bs4 import BeautifulSoup
import requests
import shutil
import emoji
import mysql.connector

#Creates connection with the DB
with open('dbkeys.txt') as dbkeys:
    host=dbkeys.readline().strip()
    user=dbkeys.readline().strip()
    password=dbkeys.readline().strip()
    database=dbkeys.readline().strip()
    dbkeys.close()
mydb = mysql.connector.connect(host=host, user=user, password=password, database=database)

mycursor = mydb.cursor()

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
def load_data(soup, page, image):
    birdname = soup.find('span', class_='Heading-main Media--hero-title').text
    birdkey = soup.find('span', class_='Heading-sub Heading-sub--sci Heading-sub--custom u-text-4-loose').text
    details = soup.find('p', class_='u-stack-sm').text
    link = page.url
    #According to character restrictions, we fit the length of the information to the maximum space available but without cutting it randomly. We search for the last available
    #dot and trim the data.
    longitud = len(birdname+birdkey+link)
    details_max = 280 - longitud
    data = details[0:details_max]
    maxdata = data.rfind('.')
    final_data = data[0:maxdata]
    save_to_database(birdname, birdkey, final_data, link, image)
    return [birdname, birdkey, final_data, link]

#Generates a string which will be the text of a tweet with the info received at the params
def gen_tweet(birdname, birdkey, final_data, link):
    return (emoji.emojize(':bird: ') +birdname+"\n"+emoji.emojize(':woman_scientist: ') +birdkey+"\n"+emoji.emojize(':information: ') +final_data+'.'+"\n"
    +emoji.emojize(':magnifying_glass_tilted_right: ')+link)

#Requests a random bird to eBird.org
def request_bird():
    imageFound = False
    #Sometimes the bird has no images. In order to avoid it this loop makes a new try every time the webpage has no images attached.
    while(imageFound == False):
        url = 'https://ebird.org/species/surprise-me'
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        imgTag = soup.find('img')
        try:
            image = imgTag['src']
            imageFound = True
            save_image(image)
            return load_data(soup, page, image)
        except:
            print('Image not found. Trying again...')

#Main function
def main():
    data=request_bird()
    return gen_tweet(data[0],data[1],data[2],data[3])

if __name__ == "__main__":
    main()