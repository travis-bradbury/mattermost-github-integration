from config import SHOW_AVATARS

class Payload(object):
    def __init__(self, data):
        self.data = data

    def user_link(self):
        name   = self.data['user']['name']
        avatar = self.data['user']['avatar_url']
        return self.create_user_link(name, url, avatar)

    def create_user_link(self, name, url, avatar):
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
        l = text.split("\n")
        result = l[0]
        if result[-1] in "[\n, \r]":
            result = result[:-1]
        if result != text:
            result += " [...]"
        return result

class Issue(Payload):
    def __init__(self, data):
        Payload.__init__(self, data)
        self.number = self.data['object_attributes']['id']
        self.title  = self.data['object_attributes']['title']
        self.url    = self.data['object_attributes']['url']
        self.body   = self.data['object_attributes']['description']

    def opened(self):
        body = self.preview(self.body)
        msg = """%s opened new issue [#%s %s](%s) in %s:
> %s""" % (self.user_link(), self.number, self.title, self.url, self.repo_link(), body)
        return msg

    def updated(self):
        body = self.preview(self.body)
        msg = """%s updated issue [#%s %s](%s) in %s:
> %s""" % (self.user_link(), self.number, self.title, self.url, self.repo_link(), body)
        return msg

    def closed(self):
        body = self.preview(self.body)
        msg = """%s closed issue [#%s %s](%s) in %s:
> %s""" % (self.user_link(), self.number, self.title, self.url, self.repo_link(), body)
        return msg

class Comment(Payload):
    def __init__(self, data):
        Payload.__init__(self, data)
        self.number = self.data['issue']['number']
        self.title  = self.data['issue']['title']
        self.url    = self.data['object_attributes']['url']
        self.body   = self.data['object_attributes']['note']

    def created(self):
        body = self.preview(self.body)
        msg = """%s commented on [#%s %s](%s): > %s""" % (self.user_link(), self.number, self.title, self.url, body)
        return msg

