"""
Helper functions to assist the views.
"""
from django.http import Http404
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from urlparse import urlparse
from urllib import urlencode
import datetime

from news.models import NewsItem
from news.conf import NEWS_ITEMS_FRONTPAGE


def get_frontpage_querymanager(request=None):
    """
    Get the querymanager containing all of the news items that could be on
    the frontpage.
    """
    if request and request.user.is_authenticated() and \
            request.user.get_profile().option_show_dead:
        querymanager = \
                NewsItem.objects.filter(date_posted__gt=(datetime_ago(weeks=4)))
    else:
        querymanager = \
                NewsItem.objects.filter(date_posted__gt=(datetime_ago(weeks=4)),
                        dead=False)

    querymanager = querymanager.order_by('-ranking', '-date_posted')

    return querymanager

def get_child_comments(comment_set, depth=0, return_dead=True):
    """ 
    Return a list of all the comments in comment_set, 
    along with all of the children of these comments.
    Return dead comment if return_dead is true.
    """
    comments = []

    for com in sorted(comment_set.all(), key=lambda cm: -cm.ranking):

        if return_dead or not com.dead:
            comments.append({'comment': com, 'depth': depth})

        if com.child_set.count():
            comments.extend(get_child_comments(com.child_set, depth+1, return_dead))
    
    return comments

def get_next_with_pages(url, page):
    """
    Takes url as a base, and urlencodes a "?page=NUM"
    part onto it, but only if it's not the first page.

    Example:
    >>> get_next_with_pages('/', 1)
    '/'
    >>> get_next_with_pages('/', 2) 
    '%2F%3Fpage%3D2'
    """
    if page == 1:
        return url
    else:
        return urlencode({'next': url + "?page=" + str(page)})[5:]

def get_pagenum(request):
    """
    This gets the page number passes on a GET request and
    makes sure it's an int.
    """
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    return page

def get_paginator_page(objects, page=1, objs_per_page=NEWS_ITEMS_FRONTPAGE):
    """
    This creates a paginator objects and returns the 
    the page created. Page number passed in as a GET arg.
    """
    paginator = Paginator(objects, objs_per_page)

    # If page request (9999) is out of range, deliver last page of results.
    try:
        front_page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        front_page = paginator.page(paginator.num_pages)

    return front_page

def datetime_ago(weeks=0, days=0, hours=0, minutes=0, seconds=0):
    """ 
    Get a datetime object for some amount of time ago.
    """
    tmdlt = datetime.timedelta(weeks * 7 + days, 
                               hours * 3600 + minutes * 60 + seconds)
    return datetime.datetime.now() - tmdlt

def improve_url(url):
    """
    This function will improve an improperly submitted url.
    Right now it only adds http to the front of a url if it
    does not already have it.
    """
    if url:
        (scheme, netloc, path, params, query, fragment) = urlparse(url)
        if not scheme:
            url = "http://" + url
    return url

def assert_or_404(boolean_val):
    """
    This is to assert something and raise an Http404 if it is false.
    """
    if not boolean_val:
        raise Http404
