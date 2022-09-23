from flask import Flask, render_template
from redisstore import store
import requests
import json
from redisstore import store
import threading

# gets the bearer token from api.json -file
file_path = './api.json'

with open(file_path) as f:
    twitter_api = json.loads(f.read())

bearer_token = twitter_api['bearer_token']

# auths with the twitter api
def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FilteredStreamPython"
    return r

# gets the previous streaming rules
def get_rules():
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))
    return response.json()

# deletes the old rules, twitter's v2 api remembers your old rules even if you stop the stream
def delete_all_rules(rules):
    if rules is None or "data" not in rules:
        return None

    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot delete rules (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    print(json.dumps(response.json()))

# set new rules for the stream
def set_rules(delete):
    # You can adjust the rules here if needed
    sample_rules = [
        {"value": "#bbsuomi"},
    ]
    payload = {"add": sample_rules}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            "Cannot add rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))

# this connects to the redisstore file
todb = store()
# gets the stream from the twitter v2 spi and calls the redis push function
def get_stream(set):
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream", auth=bearer_oauth, stream=True,
    )
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(
            "Cannot get stream (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    for response_line in response.iter_lines():
        if response_line:
            json_response = json.loads(response_line)
            tweet_data = json.dumps(json_response["data"]["text"], indent=4, sort_keys=True, ensure_ascii=False)
            print(tweet_data)
            todb.push(tweet_data)



def main():
    rules = get_rules()
    delete = delete_all_rules(rules)
    set = set_rules(delete)
    get_stream(set)

app = Flask(__name__)
db = store()

@app.route('/')
def index():
# this sorts the tweets so the ones with matcher go to the top of the stream
    tweets = db.tweets()
    matcher = [' on ', ' on.', ' on!', ' on?']
    sortedtweets = [s for s in tweets if any(xs in s for xs in matcher)]
    nomatch = [x for x in tweets if x not in sortedtweets]
    sortedtweets.extend(nomatch)
    return render_template('index.html', sortedtweets=sortedtweets)

# this allows the stream and flask app run at the same time even in a container

def run_app():
    app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)

if __name__ == '__main__':
    first_thread = threading.Thread(target=run_app)
    second_thread = threading.Thread(target=main)
    first_thread.start()
    second_thread.start()
    
