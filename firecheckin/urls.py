# -*- coding: utf-8 -*-
# firecheckin.urls

"""
Definitions for URL routes, Kay-style
"""

from werkzeug.routing import (
  Map, Rule, Submount,
  EndpointPrefix, RuleTemplate,
)

def make_rules():
  return [
    EndpointPrefix('firecheckin/', [
      Rule('/', endpoint='index'),
      Rule('/mobile/', endpoint='mobile'),
      Rule('/fe_connect/', endpoint='fe_connect'),
      Rule('/fe_request_token_ready', endpoint='fe_request_token_ready'),
      Rule('/fs_connect/', endpoint='fs_connect'),
      Rule('/fs_request_token_ready', endpoint='fs_request_token_ready'),
      Rule('/sync/', endpoint='sync'),
      Rule('/syncworker/', endpoint='syncworker'),
      Rule('/deleteme/', endpoint='deleteme'),
    ]),
  ]

all_views = {
  'firecheckin/index': 'firecheckin.views.index',
  'firecheckin/mobile': 'firecheckin.views.mobile',
  'firecheckin/fe_connect': 'firecheckin.views.fe_connect',
  'firecheckin/fe_request_token_ready': 'firecheckin.views.fe_request_token_ready',
  'firecheckin/fs_connect': 'firecheckin.views.fs_connect',
  'firecheckin/fs_request_token_ready': 'firecheckin.views.fs_request_token_ready',
  'firecheckin/sync': 'firecheckin.views.sync',
  'firecheckin/syncworker': 'firecheckin.views.syncworker',
  'firecheckin/deleteme': 'firecheckin.views.deleteme',  
  
}
