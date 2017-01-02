import re

from config import SHOW_AVATARS
from config import GITLAB_URL

class Payload(object):
    def __init__(self, data):
        self.data = data

    def user_link(self):
        name   = self.data['user']['name']
        avatar = self.data['user']['avatar_url']
        return self.create_user_link(name, avatar)

    def create_user_link(self, name, avatar):
        if SHOW_AVATARS:
            return "![](%s) [%s]" % (avatar, name)
        return "[%s]" % (name)

    def repo_link(self):
        name = self.data['repository']['name']
        url  = self.data['repository']['url']
        return "[%s](%s)" % (name, url)

    def preview(self, text):
        if not text:
            return text
	text = self.fix_gitlab_links(text);
        l = text.split("\n")
        result = l[0]
        if result[-1] in "[\n, \r]":
            result = result[:-1]
        if result != text:
            result += " [...]"
        return result

    def fix_gitlab_links(self, text):
        matches = re.findall(r'(\[[^]]*\]\s*\((/[^)]+)\))', text)

        for (replace_string, link) in matches:
            new_string = replace_string.replace(link, GITLAB_URL + link)
            text = text.replace(replace_string, new_string)

        return text

class Issue(Payload):
    def __init__(self, data):
        Payload.__init__(self, data)
        self.number = self.data['object_attributes']['iid']
        self.title = self.data['object_attributes']['title']
        self.url    = self.data['object_attributes']['url']
        self.body   = self.data['object_attributes']['description']

    def opened(self):
        body = self.preview(self.body)
        msg = """%s opened new issue [#%s %s](%s) in %s: %s""" % (self.user_link(), self.number, self.title, self.url, self.repo_link(), body)
        return msg

    def updated(self):
        body = self.preview(self.body)
        msg = """%s updated issue [#%s %s](%s) in %s: %s""" % (self.user_link(), self.number, self.title, self.url, self.repo_link(), body)
        return msg

    def closed(self):
        body = self.preview(self.body)
        msg = """%s closed issue [#%s %s](%s) in %s: %s""" % (self.user_link(), self.number, self.title, self.url, self.repo_link(), body)
        return msg

class Push(Payload):
    def __init__(self, data):
        Payload.__init__(self, data)
	self.branch = self.data['ref'].replace('refs/heads/', '')

    def default(self):
        msg = """%s pushed to %s -> %s\n""" % (self.data['user_name'], self.repo_link(), self.branch)
	for commit in self.data['commits']:
            msg += """* [%s](%s): %s\n""" % (commit['id'][:7], commit['url'], commit['message'].split("\n")[0])
        return msg

class Comment(Payload):
    def __init__(self, data):
        Payload.__init__(self, data)
        if 'commit' in self.data:
            self.number = self.data['commit']['id']
	    self.title = self.data['commit']['title']
        elif 'merge_request' in self.data:
            self.number = self.data['merge_request']['id']
	    self.title = self.data['merge_request']['title']
        elif 'issue' in self.data:
            self.number = self.data['issue']['iid']
	    self.title = self.data['issue']['title']
        else:
            self.number = self.data['object_attributes']['id']
            self.title = ""
        self.url    = self.data['object_attributes']['url']
        self.body   = self.data['object_attributes']['note']

    def default(self):
        body = self.preview(self.body)
        msg = """%s commented on [#%s %s](%s): %s""" % (self.user_link(), self.number, self.title, self.url, body)
        return msg

class Pipeline(Payload):
    def __init__(self, data):
        Payload.__init__(self, data)
	self.number = self.data['object_attributes']['id']
	self.ref = self.data['object_attributes']['ref']
	self.status = self.data['object_attributes']['status']
	self.commit = """[%s](%s): %s""" % (self.data['commit']['id'], self.data['commit']['url'], self.data['commit']['message'])

    def default(self):
        msg = """%s %s on %s\n""" % (self.ref, self.status, self.commit)
	for build in self.data['builds']:
	    msg += """* %s: %s %s\n""" % (build['stage'], build['name'], build['status'])
        return msg


