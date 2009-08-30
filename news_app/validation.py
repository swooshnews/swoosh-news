"""
Validation functions to assist the views.
"""
from django.core.urlresolvers import resolve, Resolver404
from django.http import Http404

from urlparse import urlparse
import re

import news.conf as news_settings
from news.helpers import assert_or_404



def valid_comment_text(comment_text):
    """
    Returns true if this comment is valid (e.g. not blank..)
    """
    # TODO: Could this be merged somehow with valid_text()?
    if comment_text == '':
        return False

    return True

def valid_email(email_address):
    """
    Returns true if the email address is valid.
    """
    if len(email_address) > news_settings.NEWS_MAX_EMAIL_LENGTH:
        return False

    return True

def valid_next_redirect(next):
    """
    This validates whether or not the value passed in as the next
    url is valid or not.
    """
    # if the next pattern can be resolved to one of my views, then 
    # it probably isn't something wrong
    try:
        (scheme, netloc, path, params, query, fragment) = urlparse(next)
        assert_or_404(scheme == '' and netloc == '')
        resolve(path)
        return True
    except Resolver404:
        return False
    except Http404:
        return False

def valid_password(password):
    """
    Returns true if password is valid.
    """
    if len(password) > news_settings.NEWS_MAX_PASSWORD_LENGTH:
        return False
    if not password:
        return False

    return True

def valid_text(text):
    """
    Checks to make sure the text is properly formed.
    """
    #TODO: This is fine for now...?
    return True

def valid_title(title):
    """
    Checks to make sure the title is properly formed.
    """
    if len(title) > news_settings.NEWS_MAX_TITLE_LENGTH:
        return False
    if not title:
        return False

    return True

def valid_url(url):
    """
    Checks to make sure the URL is properly formed.
    This is used when submitting news items.
    """
    if len(url) > news_settings.NEWS_MAX_URL_LENGTH:
        return False
    if not url.startswith(("http://", "https://")):
        return False

    (scheme, netloc, path, params, query, fragment) = urlparse(url)
    if not "." in netloc:
        return False

    # test to make sure that you can't just get the link "www."
    # netloc.split(".") returns something like ['www', 'google', 'com'].
    # This all() would return false if it was something like ['www', ''].
    if not all(len(dom) > 0 for dom in netloc.split(".")):
        return False

    return True

def valid_username(username):
    """
    Returns true if a username is valid.
    (It only contains specific characters.)
    """
    # this should only match usernames that match \w 
    # (because that is what a username is defined as in urls.py)
    if not re.match('^\w+$', username):
        return False

    if len(username) > news_settings.NEWS_MAX_USERNAME_LENGTH:
        return False

    return True

