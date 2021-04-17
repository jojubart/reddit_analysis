# Reddit Analysis

## General Idea

get reddit posts and comments and analyze them - looking for trends
The idea of this little project is aggregating the top posts and their comments from selected subreddits. 
Then the data is used for analyzing trends, looking for subreddit clusters and explorative data analysis in general.

## Getting the Data

The official reddit API and the [PRAW](https://praw.readthedocs.io/en/latest/) wrapper around it will help us to 
get information about subreddits, get submissions and their comments, including scores, the comment and post authors
and some more interesting data.

### Batch vs. Streaming Analysis

When streaming live data I won't get the score of posts and comments and can't determine public opinion.
Sounds like that's just half the fun - I want to find out what gets the people riled up!
Streaming the data would allow me to get every single submission and comment from the selected subreddits,
even the ones being deleted later on.
With batch analysis, I could just get the most popular posts (10-20) per day per subreddit.
Data could be scraped just once a day/week. Posts and comments would have their (almost) final score.
This will provide a robust and cost effective solution, which is why I'm picking this one.
I could also batch all the submissions per day, but I'm mainly interested in the popular content anyway
for the analysis, so I don't really consider it a loss to miss out on thousands of submission without any
upvotes, comments or general reactions to them.

#### PRAW

Let's see what getting reddit data actually looks like.
First you'll have to [register your reddit app](https://www.reddit.com/prefs/apps/). There you'll get your client_id and client_secret.
First you need these credentials and your reddit username and password to create a reddit instance.
I'd strongly advise you to put that information in a separate .ini file and to parse it from there.
Then add the .ini file to your .gitignore file to avoid leaking your password when commiting this project at some point to a public repository.
Let's start off really basic and print out the subreddit's name,
the top submission of the last day and all of its comments for two subreddits and their top post of the past day.

```python
import praw
import configparser

#################################################
subreddits = ["aws", "askhistorians"]
num_posts = 1
###################################################

config = configparser.ConfigParser()
config.read("config.ini")

reddit = praw.Reddit(
    client_id=config["PRAW"]["client_id"],
    client_secret=config["PRAW"]["client_secret"],
    user_agent=config["PRAW"]["user_agent"],
    username=config["PRAW"]["username"],
    password=config["PRAW"]["password"],
)

for subreddit in subreddits:
    subreddit = reddit.subreddit(subreddit)
    print(subreddit.display_name)
    for submission in subreddit.top("day", limit=num_posts):
        print(submission.title)

        # show all comments and present them as a list we can loop through
        submission.comments.replace_more(limit=None)
        all_comments = submission.comments.list()

        for comment in submission.comments.list():
            print(comment.body)

```

Great, that was easy!
Now we can print out the top posts and their comments. 
Let's add some structure to that. We could introduce separate data structures for subreddits, submissions and comments, but we will opt to save them right away as dicts, with the goal in mind to transfer them to AWS later on in JSON format.

```python
#....
for subreddit in subreddits:

    subreddit = reddit.subreddit(subreddit)
    subreddit_json = {
        "url": subreddit.url,
        "title": subreddit.title,
        "subscribers": subreddit.subscribers,
        "description_short": subreddit.public_description,
        "description_long": subreddit.description,
        "creation_date": str(datetime.utcfromtimestamp(
            subreddit.created_utc).strftime('%Y/%m/%d')),
        "over18": subreddit.over18,
    }

    for submission in subreddit.top("day", limit=num_posts):
        timestamp_submssion = str(datetime.utcfromtimestamp(
            submission.created_utc).strftime('%Y/%m/%d %H:%M:%S'))
        submission_json = {
            "timestamp": timestamp_submssion,
            "submission_id": submission.id,
            "subreddit": submission.subreddit.url,
            "title": submission.title,
            "selftext": submission.selftext,
            "score": submission.score,
            "stickied": submission.stickied,
            "author": str(submission.author),
            "url": submission.url,
            "domain": submission.domain,
            "upvote_ratio": submission.upvote_ratio,
            "awards": submission.total_awards_received,
            "current_subreddit_subscribers": submission.subreddit_subscribers,
            "num_comments": submission.num_comments,
            "selfpost": submission.is_self,
            "distinguished": submission.distinguished,
            "num_awards": submission.total_awards_received

        }

        all_comments = submission.comments.list()
        for comment in submission.comments.list():

            timestamp_comment = str(datetime.utcfromtimestamp(
                comment.created_utc).strftime('%Y/%m/%d %H:%M:%S'))
            comment_json = {
                "submission_id": submission.id,
                "timestamp": timestamp_comment,
                "comment_id": comment.id,
                "subreddit": str(comment.subreddit),
                "comment_body": comment.body,
                "author": str(comment.author),
                "score": comment.score,
                "controversiality": comment.controversiality,
                "num_awards": comment.total_awards_received,
                "is_submitter": comment.is_submitter,
                "is_root": comment.is_root,
                "stickied": comment.stickied,
            }
```

Now we have all kinds of information for comments and posts. Scores, number of awards, timestamps and lots more.
Notice how we're saving the subreddit subscriber count in the submission section additionally to the subreddit_json subscriber count.
This way we'll know the number of subscribers a subreddit had when posts were made way back in the past.
All the information so far is given to us straight from reddit, unfiltered and not modified.
We'd also like to add some immediate insights into the data points. 
The sentiment of a comment is one such metric that comes to mind immediately. With all the Python packages nowadays out there, this can be done in just a couple of lines. 
On simple but powerful Natural Language Processing (NLP) package is [TextBlob](https://textblob.readthedocs.io/en/dev/index.html). Additionally we want to add a flag signalling comments and submission titles/descriptions containing profanity.

```bash
pip install -U textblob
python -m textblob.download_corpora
pip install better_profanity
```

Let's add sentiment and polarity scores to all comments:

```python
from textblob import TextBlob
from better_profanity import profanity
### .....
for subreddit in subreddits:
    ###....
    for submission in subreddit.top("day", limit=num_posts):
        ###...
        submission_json = {
            ###...
        "contains_profanity": profanity.contains_profanity(submission.title + " " + submission.selftext)

        }
        for comment in submission.comments.list():
            blob = TextBlob(comment.body)
            ###...
            comment_json = {
                ###...
                "subjectivity": blob.subjectivity, # [0.0, 1.0], 0.0: very objective
                "polarity": blob.polarity # [-1.0, 1.0]
                "contains_profanity": profanity.contains_profanity(comment.body),
                
            }



## Storage

This one's a little bit tricky since we have lots of options, so let's explore them one by one

### RDS

Using RDS with e.g. a PostgreSQL DB would be a possible solution that gives us great performance,
especially in the beginning when we don't have lots of data. We could organize our tables in a space effective
manner using the 3rd Normal Form and would have tidy and easy to query data. Awesome, looks like a great way to go!
Well, if you like the smell of burning cash at least. Provisioning lots of storage for RDS comes at quite a cost. 
Let's say we fill 10 TB of space at some point, at \$0.115/GB that's \$1150 a month for storage alone. So while RDS could be 
the perfect solution for scraping small subsets of reddit regularly, it might not be ideal for us. 

### DynamoDB

The goal of the data aggregation is getting structured data for subreddits, submission, comments, users and
make changes as easy as possible. In DynamoDB on the other hand, we basically have one big table with all the
data.
Let's say the title message of a subreddit changes? That shouldn't be a problem, right? Well, in DynamoDB we will
have to change every submission from that subreddit. And all the comments. So, uhm, all entries associated with that
subreddit, which could be millions. r/AskReddit gets more than 100k comments a day - keeping everything in one column
will just be unneccessary and needlessly hard to maintain. 
What about a relational data store? Here we have a 'subreddit' table, with just one entry per subreddit. 
The other tables just have references to that table. Updating subreddit information therefore is just updating one row.
"Why can't we just do that in DynamoDB then? Create a table for each category? Submission, Subreddits, Comments,...?"
Well you could do that but it's really impractical to join them together again. NoSQL is not really meant to do
complicated JOIN operations. You could use an ETL service like Glue to get the data to S3, do the analysis with Athena
and you're good to go. But now you're storing data in DynamoDB and S3, pay both, pay for Glue jobs, pay for Athena 
Scans and have all the hassle of setting this system up and maintaining it.

### S3 + Athena

Now you might think "Why not just skip the DynamoDB and Glue part and just save our data in S3 right away? 
Query using Athena and we're good."
Let's see how much this could cost us first. S3 Standard is $0.023/GB a month, for 10TB that's $230 for 10TB a month
for data storage, which still seems reasonable for that much data. Plus there's no limit. You can go crazy and scrape
all the reddit post data including images and videos if you have that kind of cash laying around. 
Since I plan on scraping
i) a small subset of subreddits
ii) just the top posts with comments from these subreddits
iii) won't save any image files
reaching 10TB should take quite some time.

What about the Athena query costs?
With Athena you pay $5.00 for each TB of scanned data. With a 10TB table that amounts to... $50 **per query**. 
Well, that's not so great.
If we compress the S3 files using GZIP, we might reduce the file size by about 2/3, which leaves us with a 3.3TB file
and a bill of about \$17 per query. Okay that's a little better already. It's a huge file after all. 
But there's another really cool thing we can do.
Athena queries scan the whole file, line by line when doing its queries, since that's the way the file is saved on disk -
row by row.
This row-based style is common practice and the way to go when manipulating (select, update, delete) an entire row.
When we're only interested in a single column on the other hand, there are file formats such as Parquet which save data
on disk	column by column instead of row by row.
This allows reading just a single (potentially really long) line when querying data. Hence, we don't necessarily read
the whole file anymore.
Let's say we are interested in a single column from our five column 10TB table. With compression (2/3 reduction) and
the Parquet file type (1/5 columns -> 4/5 reduction) we will only need to pay for a $1/3*1/5*10TB = 0.667TB$ data scan.
That amounts to about \$3.5 instead of the \$50 we'd need to pay uncompressed and with row-based file types.
So far so good!
We could also use Redshift Spectrum which has the same price per query as Athena, but then we'd also have to run
a Redshift cluster and that adds some cost and has no immediate benefits unless we use that cluster elsewhere too.

That settles it. We'll use S3 as a data lake storage and Athena to do the queries. 


####

