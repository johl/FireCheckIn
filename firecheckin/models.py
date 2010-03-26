# -*- coding: utf-8 -*-
# firecheckin.models
"""
This is the model for our datastore entry called Token, storing OAuth info for the user
"""

from google.appengine.ext import db

class Token(db.Model):
    user = db.StringProperty()
    fe_request_token = db.StringProperty()
    fe_token = db.StringProperty()
    fs_request_token = db.StringProperty()
    fs_token = db.StringProperty()
    fs_user_token = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
