import os
import requests
from flask import Flask
from flask import request
import json
import config
import hmac
import hashlib

from payload import Issue, Comment

app = Flask(__name__)

SECRET = hmac.new(config.SECRET, digestmod=hashlib.sha1) if config.SECRET else None

@app.route(config.SERVER['hook'] or "/", methods=['POST'])
def root():
    if request.json is None:
       print 'Invalid Content-Type'
       return 'Content-Type must be application/json and the request body must contain valid JSON', 400

    if SECRET:
        signature = request.headers.get('X-Gitlab-Token', None)
        sig2 = SECRET.copy()
        sig2.update(request.data)

        if signature is None or sig2.hexdigest() != signature.split('=')[1]:
            return 'Invalid or missing X-Hub-Signature', 400

    data = request.json
    event = request.headers['X-Gitlab-Event']

    print event
    print data

    msg = ""
    if event == "Issue Hook":
        if data['object_attributes']['action'] == "open":
            msg = Issue(data).opened()
        elif data['object_attributes']['action'] == "close":
            msg = Issue(data).closed()
        elif data['object_attributes']['action'] == "update":
            msg = Issue(data).updated()
    elif event == "Note Hook":
        if data['object_attributes']['noteable_type'] == "Issue":
            msg = 'Test'
            #msg = Comment(data).created()

    print msg

    if msg:
        hook_info = get_hook_info(data)
        if hook_info:
            url, channel = get_hook_info(data)
            post(msg, url, channel)
            print "Notification successfully posted to Mattermost"
            return "Notification successfully posted to Mattermost"
        else:
            print "Notification ignored (repository is blacklisted)."
            return "Notification ignored (repository is blacklisted)."
    else:
        return "Not implemented", 400

def post(text, url, channel):
    data = {}
    data['text'] = text
    data['channel'] = channel
    data['username'] = config.USERNAME
    data['icon_url'] = config.ICON_URL

    headers = {'Content-Type': 'application/json'}
    r = requests.post(url, headers=headers, data=json.dumps(data), verify=False)

    if r.status_code is not requests.codes.ok:
        print 'Encountered error posting to Mattermost URL %s, status=%d, response_body=%s' % (url, r.status_code, r.json())

def get_hook_info(data):
    if 'repository' in data:
        repo = data['repository']['full_name']
        if repo in config.MATTERMOST_WEBHOOK_URLS:
            return config.MATTERMOST_WEBHOOK_URLS[repo]
    if 'organization' in data:
        org = data['organization']['login']
        if org in config.MATTERMOST_WEBHOOK_URLS:
            return config.MATTERMOST_WEBHOOK_URLS[org]
    if 'repository' in data:
        if 'login' in data['repository']['owner']:
            owner = data['repository']['owner']['login']
            if owner in config.MATTERMOST_WEBHOOK_URLS:
                return config.MATTERMOST_WEBHOOK_URLS[owner]
        if 'name' in data['repository']['owner']:
            owner = data['repository']['owner']['name']
            if owner in config.MATTERMOST_WEBHOOK_URLS:
                return config.MATTERMOST_WEBHOOK_URLS[owner]
    return config.MATTERMOST_WEBHOOK_URLS['default']


if __name__ == "__main__":
    app.run(
        host=config.SERVER['address'] or "0.0.0.0"
    ,   port=config.SERVER['port'] or 5000
    ,   debug=False
    )
