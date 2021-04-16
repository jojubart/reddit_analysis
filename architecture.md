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

```python
import praw
from datetime import datetime

reddit = praw.Reddit(
    client_id="",
    client_secret="",
    user_agent="",
    username="",
    password="",
)
```

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

