# -*- coding: utf-8 -*-
__doc__ = 'Load browser cookies into a cookiejar'

import os
import sys
import time
import glob
import http.cookiejar
from contextlib import contextmanager
import tempfile
try:
    import json
except ImportError:
    import simplejson as json
try:
    # should use pysqlite2 to read the cookies.sqlite on Windows
    # otherwise will raise the "sqlite3.DatabaseError: file is encrypted or is not a database" exception
    from pysqlite2 import dbapi2 as sqlite3
except ImportError:
    import sqlite3

import keyring
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES


class BrowserCookieError(Exception):
    pass


@contextmanager
def create_local_copy(cookie_file):
    """Make a local copy of the sqlite cookie database and return the new filename.
    This is necessary in case this database is still being written to while the user browses
    to avoid sqlite locking errors.
    """
    # check if cookie file exists
    if os.path.exists(cookie_file):
        # copy to random name in tmp folder
        tmp_cookie_file = tempfile.NamedTemporaryFile(suffix='.sqlite').name
        open(tmp_cookie_file, 'wb').write(open(cookie_file, 'rb').read())
        yield tmp_cookie_file
    else:
        raise BrowserCookieError('Can not find cookie file at: ' + cookie_file)

    os.remove(tmp_cookie_file)


class BrowserCookieLoader(object):
    def __init__(self, cookie_files=None):
        cookie_files = cookie_files or self.find_cookie_files()
        self.cookie_files = list(cookie_files)

    def find_cookie_files(self):
        '''Return a list of cookie file locations valid for this loader'''
        raise NotImplementedError

    def get_cookies(self):
        '''Return all cookies (May include duplicates from different sources)'''
        raise NotImplementedError

    def load(self):
        '''Load cookies into a cookiejar'''
        cookie_jar = http.cookiejar.CookieJar()
        for cookie in self.get_cookies():
            cookie_jar.set_cookie(cookie)
        return cookie_jar


class Chrome(BrowserCookieLoader):
    def __str__(self):
        return 'chrome'

    def find_cookie_files(self):
        for pattern in [
            os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/Cookies'),
            os.path.expanduser('~/.config/chromium/Default/Cookies'),
            os.path.expanduser('~/.config/chromium/Profile */Cookies'),
            os.path.expanduser('~/.config/google-chrome/Default/Cookies'),
            os.path.expanduser('~/.config/google-chrome/Profile */Cookies'),
            os.path.join(os.getenv('APPDATA', ''), r'..\Local\Google\Chrome\User Data\Default\Cookies'),
        ]:
            for result in glob.glob(pattern):
                yield result

    def get_cookies(self):
        salt = b'saltysalt'
        length = 16
        if sys.platform == 'darwin':
            # running Chrome on OSX
            my_pass = keyring.get_password('Chrome Safe Storage', 'Chrome')
            my_pass = my_pass.encode('utf8')
            iterations = 1003
            key = PBKDF2(my_pass, salt, length, iterations)

        elif sys.platform.startswith('linux'):
            # running Chrome on Linux
            my_pass = 'peanuts'.encode('utf8')
            iterations = 1
            key = PBKDF2(my_pass, salt, length, iterations)

        elif sys.platform == 'win32':
            key = None
        else:
            raise BrowserCookieError('Unsupported operating system: ' + sys.platform)

        for cookie_file in self.cookie_files:
            with create_local_copy(cookie_file) as tmp_cookie_file:
                con = sqlite3.connect(tmp_cookie_file)
                cur = con.cursor()
                cur.execute('SELECT host_key, path, secure, expires_utc, name, value, encrypted_value FROM cookies;')
                for item in cur.fetchall():
                    host, path, secure, expires, name = item[:5]
                    value = self._decrypt(item[5], item[6], key=key)
                    yield create_cookie(host, path, secure, expires, name, value)
                con.close()

    def _decrypt(self, value, encrypted_value, key):
        """Decrypt encoded cookies
        """
        if (sys.platform == 'darwin') or sys.platform.startswith('linux'):
            if value or (encrypted_value[:3] != b'v10'):
                return value

            # Encrypted cookies should be prefixed with 'v10' according to the
            # Chromium code. Strip it off.
            encrypted_value = encrypted_value[3:]

            # Strip padding by taking off number indicated by padding
            # eg if last is '\x0e' then ord('\x0e') == 14, so take off 14.
            # You'll need to change this function to use ord() for python2.
            def clean(x):
                return x[:-ord(x[-1])]

            iv = b' ' * 16
            cipher = AES.new(key, AES.MODE_CBC, IV=iv)
            decrypted = cipher.decrypt(encrypted_value)
            return clean(decrypted)
        else:
            #Must be win32 (on win32, all chrome cookies are encrypted)
            try:
                import win32crypt
            except ImportError:
                raise BrowserCookieError('win32crypt must be available to decrypt Chrome cookie on Windows')
            return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1]#.decode("utf-8")


class Firefox(BrowserCookieLoader):
    def __str__(self):
        return 'firefox'

    def find_cookie_files(self):
        if sys.platform == 'darwin':
            cookie_files = glob.glob(os.path.expanduser('~/Library/Application Support/Firefox/Profiles/*.default/cookies.sqlite'))
        elif sys.platform.startswith('linux'):
            cookie_files = glob.glob(os.path.expanduser('~/.mozilla/firefox/*.default*/cookies.sqlite'))
        elif sys.platform == 'win32':
            cookie_files = glob.glob(os.path.join(os.getenv('PROGRAMFILES', ''), 'Mozilla Firefox/profile/cookies.sqlite')) or \
                           glob.glob(os.path.join(os.getenv('PROGRAMFILES(X86)', ''), 'Mozilla Firefox/profile/cookies.sqlite')) or \
                           glob.glob(os.path.join(os.getenv('APPDATA', ''), 'Mozilla/Firefox/Profiles/*.default/cookies.sqlite'))
        else:
            raise BrowserCookieError('Unsupported operating system: ' + sys.platform)
        if cookie_files:
            return cookie_files
        else:
            raise BrowserCookieError('Failed to find Firefox cookies')

    def get_cookies(self):
        for cookie_file in self.cookie_files:
            with create_local_copy(cookie_file) as tmp_cookie_file:
                con = sqlite3.connect(tmp_cookie_file)
                cur = con.cursor()
                cur.execute('select host, path, isSecure, expiry, name, value from moz_cookies')

                for item in cur.fetchall():
                    yield create_cookie(*item)
                con.close()

                # current sessions are saved in sessionstore.js
                session_file = os.path.join(os.path.dirname(cookie_file),'sessionstore-backups', 'recovery.js')
                if os.path.exists(session_file):
                    try:
                        json_data = json.loads(open(session_file, 'rb').read())
                    except ValueError as e:
                        print('Error parsing firefox session JSON:', str(e))
                    else:
                        expires = str(int(time.time()) + 3600 * 24 * 7)
                        for window in json_data.get('windows', []):
                            for cookie in window.get('cookies', []):
                                yield create_cookie(cookie.get('host', ''), cookie.get('path', ''), False, expires, cookie.get('name', ''), cookie.get('value', ''))
                else:
                    print('Firefox session filename does not exist:', session_file)


def create_cookie(host, path, secure, expires, name, value):
    """Shortcut function to create a cookie
    """
    return http.cookiejar.Cookie(0, name, value, None, False, host, host.startswith('.'), host.startswith('.'), path, True, secure, expires, False, None, None, {})


def chrome(cookie_file=None):
    """Returns a cookiejar of the cookies used by Chrome
    """
    return Chrome(cookie_file).load()


def firefox(cookie_file=None):
    """Returns a cookiejar of the cookies and sessions used by Firefox
    """
    return Firefox(cookie_file).load()


def _get_cookies():
    '''Return all cookies from all browsers'''
    for klass in [Chrome, Firefox]:
        try:
            for cookie in klass().get_cookies():
                yield cookie
        except BrowserCookieError:
            pass


def load():
    """Try to load cookies from all supported browsers and return combined cookiejar
    """
    cookie_jar = http.cookiejar.CookieJar()

    for cookie in sorted(_get_cookies(), key=lambda cookie: cookie.expires):
        cookie_jar.set_cookie(cookie)

    return cookie_jar

if __name__ == "__main__":
	url = 'http://stackoverflow.com/'
	url = 'http://icampus.univ-paris3.fr/course/view.php?id=1535'
	#url = 'https://www.google.fr'
	import requests
	#cj = firefox()
	cj = chrome()
	print(cj)
	r = requests.get(url, cookies=cj)
	
	
	#import urllib2
	##cj = chrome()
	#cj = firefox()
	#opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	#
	##print 'hoju' in urllib2.urlopen(url).read()
	#html = opener.open(url).read()
	print('kmgrds' in r.content or "gerdes" in r.content)
	open('test.html', 'w').write(r.content)
	