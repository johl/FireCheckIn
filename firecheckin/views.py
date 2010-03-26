# -*- coding: utf-8 -*-
# firecheckin.views

import logging
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
from werkzeug import (
  unescape, redirect, Response,
)
from werkzeug.exceptions import (
  NotFound, MethodNotAllowed, BadRequest
)

from kay.utils import (
  render_to_response, reverse,
  get_by_key_name_or_404, get_by_id_or_404,
  to_utc, to_local_timezone, url_for, raise_on_dev
)
from kay.i18n import gettext as _
from kay.auth.decorators import login_required

from kay.utils import render_to_response
import oauth, httplib
from fireeagle_api import FireEagle
import foursquare
import time, datetime
import ustimezones
import rfc822
from models import Token

try:
    from oauth_settings import *
except:
    """
    Here's the place to include your configuration.
    Get your keys, secrets, and callback URLs 
    from Fire Eagle and Foursquare and fill them in below.
    """
    # Configuration for Fire Eagle
    FE_CALLBACK_URL = 'http://mydomain.com/fe_request_token_ready'
    FE_CONSUMER_KEY = 'XXXXX'
    FE_CONSUMER_SECRET= 'XXXXX'
    # Configuration for Foursquare
    FS_CALLBACK_URL = 'http://mydomain.com/fs_request_token_ready'
    FS_CONSUMER_KEY = 'XXXXX'
    FS_CONSUMER_SECRET = 'XXXXX'

def index(request):
    """
    Render the single landing page we have in FireCheckIn. Fill in information on the state
    of the connections to Fire Eagle and Foursquare and see if the user is logged in.
    """
    fireeagle_connected = False
    foursquare_connected = False
    if request.user.is_anonymous():
        return render_to_response('firecheckin/index.html',  { 'fireeagle_connected': fireeagle_connected,
                                                 'foursquare_connected': foursquare_connected})
    else:
        if ( Token.gql( "WHERE user = :1", str(request.user) ).get() != None ):
              token = Token.gql( "WHERE user = :1", str(request.user) ).get()
              if ( token.fe_token ):
                  fireeagle_connected = True
              if ( token.fs_token ):
                  foursquare_connected = True
        return render_to_response('firecheckin/index.html',  { 'fireeagle_connected': fireeagle_connected,
                                                 'foursquare_connected': foursquare_connected})

@login_required
def fe_connect(request):
  """
  Do the OAuth dance for Fire Eagle!
  """
  CONSUMER_KEY = FE_CONSUMER_KEY
  CONSUMER_SECRET = FE_CONSUMER_SECRET
  CALLBACK_URL = FE_CALLBACK_URL
  fe = FireEagle( CONSUMER_KEY, CONSUMER_SECRET )
  request_token = fe.request_token( oauth_callback=CALLBACK_URL )
  if ( Token.gql( "WHERE user = :1", str(request.user) ).get() != None ):
      token = Token.gql( "WHERE user = :1", str(request.user) ).get()
  else:
    token = Token()
  token.user = str(request.user)
  token.fe_request_token = str(request_token)
  token.put()
  auth_url = fe.authorize( request_token, oauth_callback=CALLBACK_URL )
  return redirect( auth_url )

@login_required
def fe_request_token_ready(request):
  """
  OAuth dance for Fire Eagle, callback URL
  """
  query = request.environ['QUERY_STRING']
  query_values = query.split("&")
  values = {}
  for qv in query_values:
      (key, value) = qv.split("=")
      values[key] = value
  oauth_verifier = values['oauth_verifier']
  oauth_token = values['oauth_token']
  CONSUMER_KEY = FE_CONSUMER_KEY
  CONSUMER_SECRET = FE_CONSUMER_SECRET
  fe = FireEagle( CONSUMER_KEY, CONSUMER_SECRET )
  token = Token.gql( "WHERE user = :1", str(request.user) ).get()
  oauth_token = oauth.OAuthToken.from_string( token.fe_request_token )
  fe = FireEagle( CONSUMER_KEY, CONSUMER_SECRET )
  access_token = fe.access_token( oauth_verifier=oauth_verifier, token=oauth_token )
  token.fe_token = str(access_token)
  token.put()
  return redirect( "/" )

@login_required
def fs_connect(request):
  """
  OAUTh dance for Foursquare
  """
  CONSUMER_KEY = FS_CONSUMER_KEY
  CONSUMER_SECRET = FS_CONSUMER_SECRET
  CALLBACK_URL = FE_CALLBACK_URL
  credentials = foursquare.OAuthCredentials(CONSUMER_KEY, CONSUMER_SECRET)
  fs = foursquare.Foursquare(credentials)
  request_token = fs.request_token( oauth_callback=CALLBACK_URL )
  if ( Token.gql( "WHERE user = :1", str(request.user) ).get() != None ):
      token = Token.gql( "WHERE user = :1", str(request.user) ).get()
  else:
    token = Token()
  token.user = str(request.user)
  token.fs_request_token = str(request_token)
  token.put()
  auth_url = fs.authorize( request_token, oauth_callback=CALLBACK_URL )
  return redirect( auth_url )

@login_required
def fs_request_token_ready(request):
  """
  OAuth dance for Foursquare, callback URL
  """
  CONSUMER_KEY = FS_CONSUMER_KEY
  CONSUMER_SECRET = FS_CONSUMER_SECRET
  token = Token.gql( "WHERE user = :1", str(request.user) ).get()
  request_values = token.fs_request_token.split("&")
  values = {}
  for rv in request_values:
      (key, value) = rv.split("=")
      values[key] = value
  oauth_token = oauth.OAuthToken.from_string( token.fs_request_token )
  request_token_key = oauth_token
  request_token_secret = values['oauth_token_secret']
  credentials = foursquare.OAuthCredentials(CONSUMER_KEY, CONSUMER_SECRET)
  fs = foursquare.Foursquare(credentials)
  user_token = fs.access_token(request_token_key)
  credentials.set_access_token(user_token)
  fs_token = "oauth_token_secret=%s&oauth_token=%s" % (request_token_secret, str(user_token))
  token.fs_token = fs_token
  token.fs_user_token = str(user_token)
  token.put()
  return redirect( "/" )

def syncworker(request):
    """
    Okay, this is the real stuff. It's the worker process for the task queue.
    Gets a user name as a parameter.
    Calls Foursquare, Fire Eagle. Compares times of last check-in. If the Foursquare check-in
    is more recent, updates Fire Eagle.
    We catch all kinds of exceptions, so users with messed up OAuth permissions won't stop
    the worker.
    """
    user = request.args.get('user')
    logging.warning('user is: %s' % str(user))
    t = Token.gql( "WHERE user = :1", str(user) ).get()
    lat = 0
    lon = 0
    try:
        token = oauth.OAuthToken.from_string( t.fe_token )
        fe = FireEagle( FE_CONSUMER_KEY, FE_CONSUMER_SECRET )
        user = fe.user( token )
        date_time = user[0]['location'][0]['located_at']
        """
        For some reasons that only Yahoo! knows, Fire Eagle logs its time and dates
        in local Californian time (including Daylight Saving Time), so we have to
        convert the thing to UTC. Crazy, huh? 
        Share my frustration at http://blog.johl.io/post/393494632/what-time-is-it
        """
        current_datetime = datetime.datetime.now(ustimezones.pacific()) # What time is it in Cali?
        fe_delta = str(current_datetime.replace(tzinfo=None) - date_time)
        credentials = foursquare.OAuthCredentials( FS_CONSUMER_KEY, FS_CONSUMER_SECRET )
        fs = foursquare.Foursquare( credentials )
        token = oauth.OAuthToken.from_string( t.fs_user_token )
        credentials.set_access_token(token)
        history = fs.history()
        date_time = history['checkins'][0]['created']
        lat = history['checkins'][0]['venue']['geolat']
        lon = history['checkins'][0]['venue']['geolong']
        current_datetime = datetime.datetime.now()
        date_time = datetime.datetime.fromtimestamp(time.mktime(rfc822.parsedate(date_time)))
        fs_delta = str(current_datetime.replace(tzinfo=None) - date_time)
    except:
        """
        So yeah, something went wrong. Let's assume we should update Fire Eagle.
        """
        logging.warning('Application error occurred with user %s', str(t.user))
        fs_delta = 0
        fe_delta = -1
    if (fs_delta < fe_delta):
      try:
        fe.update( lat=lat, lon=lon, token=oauth.OAuthToken.from_string( t.fe_token ) )
      except:
        """
        Can't update Fire Eagle. Whatever.
        """
        logging.warning('Application error occurred with user %s', str(t.user))
    return render_to_response('firecheckin/index.html')

def sync(request):
  """
  It's the cron job that gets run every 2 minutes (or on request). Iterates over users and
  queues tasks to sync. Will only 'iterate' over the current user
  if called by a logged in user.
  """
  tokens = []
  if (request.user.is_anonymous()):
      tokens = Token.all().fetch(1000)
  else:
      tokens.append(Token.gql( "WHERE user = :1", str(request.user) ).get())
  for t in tokens:
      taskqueue.add(url='/syncworker/?user=%s' % str(t.user), method='GET')
  """
  We cannot return a redirect when called anonymously as a cron job.
  Google App Engine will complain about 'Too many continues.'
  """
  if (request.user.is_anonymous()):
      return render_to_response('firecheckin/index.html')
  else:
      return redirect( "/" )

def deleteme(request):
    """
    Remove the currently logged in user from our database and log them out. 
    Privacy, you know? Don't request this casually :)
    """
    if (not (request.user.is_anonymous())):
        logout = users.create_logout_url( "/" )
        db.delete(Token.gql( "WHERE user = :1", str(request.user) ).get())
        return redirect( logout )
    else:
        return redirect( "/" )
