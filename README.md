# Info
A simple app that connects to twitter's v2 api to stream tweets based on a rule.
Saves the stream to redis and displays it in flask.
You can also organize tweets whether they contain a certain string or not. You can modify these word/words in app.py's matcher variable.

# Installation
First you need to set up a redis server locally.

```
pip install -r requirements.txt
```
```
python streamer.py
```
```
python app.py
```
You can also containerize the app using Dockerfile