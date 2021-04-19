import praw
import configparser
from textblob import TextBlob
from better_profanity import profanity
import boto3
from botocore.exceptions import ClientError
import json
import logging
from datetime import datetime

#################################################
BUCKET_NAME = "rebuzzz"
subreddits = ["aws", "askhistorians"]
num_posts = 2
region_name = "eu-central-1"
delivery_stream_name = "reddit-stream"
debug = True
###################################################

config = configparser.ConfigParser()
config.read("config.ini")

firehose_client = boto3.client("firehose", region_name=region_name)
LOG_FILENAME = "/tmp/reddit_stream.log"
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)

reddit = praw.Reddit(
    client_id=config["PRAW"]["client_id"],
    client_secret=config["PRAW"]["client_secret"],
    user_agent=config["PRAW"]["user_agent"],
    username=config["PRAW"]["username"],
    password=config["PRAW"]["password"],
)


def process_firehose(json_entry):
    try:
        response = firehose_client.put_record(
            DeliveryStreamName=delivery_stream_name,
            Record={
                "Data": (json.dumps(json_entry))
            }
        )
        logging.info(response)
    except Exception:
        logging.exception("Problem pushing to firehose")


def s3_upload(path, file_name, json_object):
    s3_client.Object(BUCKET_NAME, path + file_name
                     ).put(Body=json.dumps(json_object, ensure_ascii=False).encode("utf-8"))


if debug:
    num_posts = 7
    subreddits = ["askhistorians"]
    s3_client = boto3.resource('s3')

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
    print(subreddit.display_name)

    s3_upload("subreddit/", f"{subreddit.title}" +
              str(datetime.now()) + ".json", subreddit_json)

    for submission in subreddit.top(time_filter="day", limit=num_posts):
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
            "num_awards": submission.total_awards_received,
            "contains_profanity": profanity.contains_profanity(submission.title + " " + submission.selftext)

        }
        s3_upload("submission/", f"{submission.title}" +
                  str(datetime.now()) + ".json", submission_json)

        submission.comments.replace_more(limit=0)  # flatten tree
        for comment in submission.comments.list():
            blob = TextBlob(comment.body)
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
                "contains_profanity": profanity.contains_profanity(comment.body),
                # [0.0, 1.0], 0.0: very objective, 1.0: very subjective
                "subjectivity": blob.subjectivity,
                "polarity": blob.polarity,  # [-1.0, 1.0]
            }
            s3_upload("comment/", f"{comment.author}" +
                      str(datetime.now()) + ".json", comment_json)
