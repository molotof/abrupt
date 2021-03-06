import re

from abrupt.color import *

try:
  import lxml.html
  has_lxml = True
except ImportError:
  has_lxml = False

class Generic:
  html_keywords = [r'Error', r'Warning', r'SQL', r'LDAP', r'Failure']
  js_keywords = [r'password', r'credential']

  def __init__(self):
    self.html_patterns = [re.compile(s, re.I) for s in self.html_keywords]
    self.js_patterns = [re.compile(s, re.I) for s in self.js_keywords]

  def cookies_in_body(self, r):
    alerts = []
    if r.response.cookies:
      for k in r.response.cookies:
        if r.response.cookies[k].value in r.response.content:
          alerts.append(error("response.content matches the cookie " + k))
    return alerts

  def parse_html(self, r):
    alerts = []
    if has_lxml:
      try:
        root = lxml.html.fromstring(r.response.content)
        content = ''.join([x for x in root.xpath("//text()") if
                            x.getparent().tag != "script"])
      except UnicodeDecodeError:
        alerts.append(stealthy("reponse.content-type says html but " \
                               "unable to parse"))
        return alerts
      except lxml.etree.ParserError:
        return alerts
    else:
      content = r.response.content
    for e in self.html_patterns:
      if e.search(content):
        if has_lxml: # We are more confident of what we've found
          alerts.append(error("response.content matches " + e.pattern))
        else:
          alerts.append(warning("response.content matches " + e.pattern))
    return alerts

  def parse_javascript(self, r):
    alerts = []
    for e in self.js_patterns:
      if e.search(r.response.content):
        alerts.append(error("response.content matches " + e.pattern))
    return alerts

  def parse(self, r):
    if r.response and r.response.content:
      if r.response.is_html:
        return self.parse_html(r) + self.cookies_in_body(r)
      if r.response.is_javascript:
        return self.parse_javascript(r)
    return []
