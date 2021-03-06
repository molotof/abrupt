import __builtin__
import os
import os.path
import sys
import glob
import ConfigParser
import ssl

CONF_DIR = os.path.expanduser("~/.abrupt/")
CERT_DIR = os.path.join(CONF_DIR, "certs")
SESSION_DIR = os.path.join(CONF_DIR, "sessions")
ARCHIVE_DIR = os.path.join(CONF_DIR, "archives")
PLUGIN_DIR = os.path.join(CONF_DIR, "plugins")

def check_config_dir():
  existed = True
  if not os.path.exists(CONF_DIR):
    os.mkdir(CONF_DIR, 0700)
  if not os.path.exists(CERT_DIR):
    os.mkdir(CERT_DIR, 0700)
    existed = False
  if not os.path.exists(os.path.join(CERT_DIR, "sites")):
    os.mkdir(os.path.join(CERT_DIR, "sites"), 0700)
  if not os.path.exists(SESSION_DIR):
    os.mkdir(SESSION_DIR, 0700)
  if not os.path.exists(ARCHIVE_DIR):
    os.mkdir(ARCHIVE_DIR, 0700)
  if not os.path.exists(PLUGIN_DIR):
    os.mkdir(PLUGIN_DIR, 0700)
  return existed

def load_plugins():
  sys.path.append(os.path.join(CONF_DIR, "plugins"))
  for f in glob.glob(os.path.join(PLUGIN_DIR, "*.py")):
    m, ext = os.path.splitext(os.path.basename(f))
    __builtin__.__dict__.update(__import__(m, globals(), locals(), ".").__dict__)
    
class Configuration(object):
  """
  Class representing the configuration of Abrupt. You should use
  the 'conf' instance. By default contains the following attributes:

    - port: default listening port
    - proxy: outgoing proxy
    - autosave: automatically save the session when exiting
    - history: keep a copy of all the requests made
    - editor, diff_editor: external editors called when editing
    - term_width: expected width of the terminal
    - ssl_version: ssl version used with the server (ssl.PROTOCOL_*)
  """
  ssl_map = {"SSLv3": ssl.PROTOCOL_SSLv3, "SSLv23": ssl.PROTOCOL_SSLv23,
             "SSLv2": ssl.PROTOCOL_SSLv2, "TLSv1": ssl.PROTOCOL_TLSv1}

  def __init__(self):
    self.ip = '127.0.0.1'
    self.port = 8080
    self.proxy = None
    self.target = None
    self.timeout = 10
    self.delay = 0
    self.autosave = True
    self.history = True
    self.color_enabled = True
    self.term_width = "auto"
    self.editor = "/usr/bin/vim"
    self.diff_editor = "/usr/bin/vimdiff"
    self.editor_args = '-c "set noeol" -c "set fileformats=dos" -b'
    self.editor_play_args = '-o2 -c "set autoread" ' \
                            '-c "autocmd CursorMoved * checktime" ' \
                            '-c "autocmd CursorHold * checktime"'
    self.ssl_hostname = None
    self.update_content_length = True
    self._ssl_version = ssl.PROTOCOL_SSLv3
    self._values = {"port": "getint", "proxy": "get", "timeout": "getint",
                    "ssl_version": "get", "autosave": "getboolean",
                    "history": "getboolean", "editor": "get",
                    "diff_editor": "get", "editor_args": "get",
                    "editor_play_args": "get", "term_width": "get",
                    "delay": "getint", "color_enabled": "getboolean",
                    "update_content_length": "getboolean", "ip": "get",
                    "target": "get", "ssl_hostname": "get"}

  def _get_ssl_version(self):
    for k, v in self.ssl_map.items():
      if v == self._ssl_version:
        return k

  def _set_ssl_version(self, v):
    try:
      self._ssl_version = self.ssl_map[v]
    except KeyError:
      raise Exception("Possible values are: " + ", ".join(self.ssl_map.keys()))

  ssl_version = property(_get_ssl_version, _set_ssl_version)

  def __repr__(self):
    return str(self)

  def __str__(self):
    return "\n".join(sorted([s + ": " + str(getattr(self, s)) for s in self._values]))

  def import_env(self):
    if "http_proxy" in os.environ:
      conf.proxy = os.environ["http_proxy"]
      print "Using", conf.proxy, "as proxy"
    if "EDITOR" in os.environ:
      conf.editor = os.environ["EDITOR"]

  def import_dict(self, d):
    for v in self._values:
      if hasattr(d, v):
        setattr(self, v, getattr(d, v))

  def load(self):
    if os.path.exists(os.path.join(CONF_DIR, "abrupt.conf")):
      c = ConfigParser.RawConfigParser()
      c.read(os.path.join(CONF_DIR, "abrupt.conf"))
      if not c.has_section("abrupt"):
        raise Exception("Configuration file corrupted")
      for k, v in self._values.items():
        if c.has_option("abrupt", k):
          setattr(self, k, getattr(c, v).__call__("abrupt", k))

  def save(self, force=False):
    import abrupt.session
    if abrupt.session.session_name != "default" and not force:
      from abrupt.color import error
      print error("""The current configuration is automatically saved when
your session is saved (see save() and conf.autosave).
To make this configuration global, use conf.save(force=True)""")
      return
    c = ConfigParser.RawConfigParser()
    c.add_section('abrupt')
    for s in self._values:
      p = getattr(self, s)
      if not p is None:
        c.set('abrupt', s, p)
    with open(os.path.join(CONF_DIR, "abrupt.conf"), "w") as f:
      c.write(f)

conf = Configuration()
