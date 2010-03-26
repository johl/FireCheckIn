What is this?
=============

FireCheckIn (http://www.firecheckin.com/) is a simple tool to sync your check-ins at Foursquare to Fire Eagle (http://fireeagle.yahoo.net/). Foursquare is part friend finder, part social city guide, part nightlife game. It can be played at http://foursquare.com. FireCheckIn is in no way official or affiliated with Foursquare.

FireCheckIn is built to be run on <a href="http://appengine.google.com/">Google App Engine</a> and is proudly written in Python, using the <a href="http://code.google.com/p/kay-framework/">Kay framework</a>, which is awesome.

To connect the user's accounts, we use OAuth, a protocol designed to keep users safe and cause headaches to developers, so we'll never know the password.

FireCheckIn was written by <a href="http://www.johl.io/">Jens Ohlig</a>.
Any questions can be sent to <a href="mailto:support@firecheckin.com">support@firecheckin.com</a>.

Further magic comes from <a href="http://github.com/wiseman/foursquare-python">foursquare-python</a> and <a href="http://github.com/SteveMarshall/fire-eagle-python-binding">fire-eagle-python-binding</a>.

Oh, and the very nifty <a href="http://oauth.googlecode.com/svn/code/python/oauth/oauth.py">oauth.py</a> by <a href="http://leahculver.com/">Leah Culver</a> was helpful, too.

About this source code
======================

This source code for the Google App Engine application written with Kay was released in the hope that it may be helpful for others. You may want to change the name of the application in app.yaml and set your OAuth settings ind firecheckin/views.py if you want to try it out.

Actually, firecheckin/views.py is where all the goodness happens. You should start reading there.
