# Ornithob0t
Ornithob0t is a Twitter bot that generates tweets from the content in the eBird.org website: <br><br>
![twitterbotflow](https://github.com/JVinuelas19/TwitterBot/assets/111135343/f368cf0d-8bb3-487d-81f7-4fff7007c0f6)
<br><br><br>
Features:
- Webscrapes concrete bird data from eBird.org and returns a fresh looking tweet respecting Twitter's character limit.
- Tweet a random bird from eBird.org and store the scrapped fields in a database.
- Tweet a random bird from the database generated by the previous feature.
- Tweet IDs management (read and write IDs from file).
- Retweet tweets from a selected account (in my case @Team_eBird , but it can retweet who you want) based on Tweet IDs to avoid redundancy retweets.
- Reply to users if they ask for a concrete bird with that bird data: <br><br><br>
- Reply to users if they use target words (This feature has no use yet)
- Reply to users if they use bad words with an advertise. (Ban system is not implemented yet)
- It can randomly tweet (1% chance) a meme bird when using the second feature: Anivia the Cryophoenix 
<br><br>
Future features will include a temporary ban system to the disrespectful replys, a database to manage these bans, thread creation with bird info instead of single tweets and an upgrade to the retweet function. 
The database can be generated with the dump file and MySQL Workbench.
The bot is currently unavailable due to Twitter API changes after the purchase of the brand by Elon Musk. I will fix it ASAP.
