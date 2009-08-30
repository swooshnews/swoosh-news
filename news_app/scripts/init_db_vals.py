#!/usr/bin/python
"""
This is used to repopulate the database after a reset or after you have
run `manage.py syncdb`.  It is used to get some test data in the database
to play around with.  It could be run like this:
$ ./init_db_vals.py

This is better than having a fixture because it is easily changable
when updating models.py, whereas a fixture has to be migrated to the
new database layout somehow.

This script is also a good way to open up a interactive session with
Django because it defines a lot of variables that are easy to work with
right away.  The variables are all defined at the bottom of the file.
To use it this way, it could be run like this:
$ ipython init_db_vals.py

This script does not change data that already exists in the database.
So, if you run this script once, then run it again, it doesn't change
anything existing in the database.  (Although, all the variables still
get initialized like they did the first time the script is run, so it
is still good for debugging even after being run the first time.)

WARNING, DO NOT RUN THIS ON A PRODUCTION DATABASE!
"""

import sys, os, random, getopt
import base

usage_explanation =["Initialize the database with default values.", 
                    "Better than fixtures because it is easily modifiable.",
                    "By default, nothing is created."]
usage_commands = ["-c, --extra-comments=N\t\tcreate N extra comments",
                  "-e, --extra-news=N\t\tcreate N extra news items",
                  "-X, --create-new\t\tcreate new items that don't exist"]

# Here are our global variables that we want available when 
# running from ipython.
# users
ice_user = None
ice_userprofile = None
bob_user = None
bob_userprofile = None
t_user = None
t_userprofile = None
# news items
ni1 = None
ni2 = None
ni3 = None
# comments
com1 = None
com2 = None
com3 = None
com4 = None
com5 = None
com6 = None
com7 = None
com8 = None
# test client
client = None
# paginator
paginator = None

create_new_objects = False

def usage():
    """ Print usage. """
    base.usage(usage_explanation, usage_commands)

def setup_path_and_args():
    """ 
    This uses base.py to setup the correct paths, in case
    this is being called on the command line and not being
    imported. It also uses base.py to get all of the command line
    arguments.  It then processes the additional args.

    Returns a dictionary of the extra args we are reading from the
    command line.  This gets passed to our main function (init_db).
    """
    extra_news_items = 0
    extra_comments = 0
    create_new_objects = False

    opts = base.get_paths_options("e:c:X", ["extra-news=", "extra-comments=", "create-new"], 
            usage)

    for opt, arg in opts:
        if opt in ("--extra-news", "-e"):
            extra_news_items = base.get_int_arg(arg,
                    "ERROR! Argument to --extra-news must be a non-negative integer.",
                    usage)
        elif opt in ("--extra-comments", "-c"):
            extra_comments = base.get_int_arg(arg,
                    "ERROR! Argument to --extra-comments must be a non-negative integer.",
                    usage)
        elif opt in ("--create-new", "-X"):
            create_new_objects = True

    return {'extra_news_items':extra_news_items, 'extra_comments':extra_comments,
            'create_new_objects': create_new_objects}


def init_db(extra_news_items=0, extra_comments=0, create_new_objects=False):
    """
    Add initial data to the database if it is not already in it.
    Just get variables that point to the initial data if it has already been
    created.
    """

    # Here are our global values that we want available when 
    # running from ipython.
    # users
    global ice_user 
    global ice_userprofile 
    global bob_user 
    global bob_userprofile 
    global t_user 
    global t_userprofile 
    # news items
    global ni1 
    global ni2 
    global ni3 
    # comments
    global com1 
    global com2 
    global com3 
    global com4 
    global com5 
    global com6 
    global com7 
    global com8 
    # test client
    global client 
    # paginator
    global paginator 
    
    from news.models import UserProfile, NewsItem, Comment, \
            Rated, Rankable
    from django.contrib.auth.models import User 

    from django.contrib.sessions.models import Session
    from django.conf import settings
    from django.core.paginator import Paginator, InvalidPage, EmptyPage
    from django.test.client import Client

    import random

    def create_user_and_profile(usrnm, psswrd, create=False):
        """ Create or get user profile. """
        usr = None
        usrprfl = None

        try:
            usr = User.objects.get(username=usrnm)
        except User.DoesNotExist:
            if create:
                usr = User.objects.create_user(usrnm, '', psswrd)

        # create user profile
        try:
            usrprfl = UserProfile.objects.get(user__username=usrnm)
        except UserProfile.DoesNotExist:
            if create:
                usrprfl = UserProfile.objects.create(user=usr)

        return (usr, usrprfl)

    def create_news_item(ni_poster, ni_title, ni_url=None, ni_text=None, create=False):
        """ Create or get a news item. """
        news_item = None

        try:
            news_item = NewsItem.objects.get(title=ni_title, poster=ni_poster, 
                    url=ni_url, text=ni_text)
        except NewsItem.DoesNotExist:
            if create:
                news_item = NewsItem.objects.create(title=ni_title, poster=ni_poster, 
                        url=ni_url, text=ni_text)
                Rated.objects.create(rankable=news_item, userprofile=ni_poster, 
                                    direction='up')
        
        return news_item

    def create_comment(com_poster, com_text, com_parent, create=False):
        """ Create or get a comment. """
        com = None
        try:
            com = Comment.objects.get(poster=com_poster, text=com_text, 
                    parent=com_parent)
        except Comment.DoesNotExist:
            if create:
                com = Comment.objects.create(poster=com_poster, text=com_text, 
                        parent=com_parent)
                Rated.objects.create(rankable=com, userprofile=com_poster, 
                                    direction='up')
        
        return com

    def create_lots_of_news_items(amount, com_poster=None):
        """ 
        Create a bunch of news items with a random rating.
        amount is the amount of news items we will create.
        com_poster is a userprofile of the poster of the news item.
        """
        rand_start = random.randint(100000, 1000000)
        for i in range(rand_start, rand_start + amount):

            if com_poster is None:
                poster = random.choice(UserProfile.objects.all())
            else:
                poster = com_poster

            ni = create_news_item(poster, str(i), 
                    ni_url=('http://' + str(i) + '.com'), create=True)
            ni.rating += random.randint(1, 100)
            ni.save()
            ni.update_ranking()

    def create_lots_of_comments(amount, com_poster=None, com_parent=None):
        """ 
        Create a bunch of comments with a random rating. 
        amount is the amount of additional comments to create.
        com_poster is a userprofile of the poster of the comment.
        """
        rand_start = random.randint(100000, 1000000)
        for i in range(rand_start, rand_start + amount):

            if com_poster is None:
                poster = random.choice(UserProfile.objects.all())
            else:
                poster = com_poster

            if com_parent is None:
                parent = random.choice(Rankable.objects.all())
            else:
                parent = com_parent

            com = create_comment(poster, str(i), parent, True)
            com.rating += random.randint(1, 100)
            com.save()
            com.update_ranking()

    def get_sessions():
        """
        Get all the current sessions.  Most recent at bottom (probably).
        """
        for sesh in Session.objects.all():
            print sesh.session_key + ": " + str(sesh.get_decoded())


    # get ice
    (ice_user, ice_userprofile) = \
            create_user_and_profile('ice', 'iceiceice', create_new_objects)
    (bob_user, bob_userprofile) = \
            create_user_and_profile('bob', 'bobbobbob', create_new_objects)
    (t_user, t_userprofile) = \
            create_user_and_profile('t', 't', create_new_objects)

    # create news items
    ni1 = create_news_item(ice_userprofile, 'google', ni_url='http://google.com',
            create=create_new_objects)
    ni2 = create_news_item(ice_userprofile, 'ms', ni_url='http://ms.com',
            create=create_new_objects)
    ni3 = create_news_item(bob_userprofile, 'yahoo', ni_url='http://www.yahoo.com',
            create=create_new_objects)

    if create_new_objects:
        create_lots_of_news_items(extra_news_items, ice_userprofile)
        create_lots_of_comments(extra_comments)

    # create comment 1 from news item 1
    com1 = create_comment(ice_userprofile, 'this is com1', ni1,
            create_new_objects)
    com2 = create_comment(ice_userprofile, 'this is com2', com1,
            create_new_objects)
    com3 = create_comment(bob_userprofile, 'this is com3', com1,
            create_new_objects)
    com4 = create_comment(bob_userprofile, 'this is com4', com2,
            create_new_objects)
    com5 = create_comment(bob_userprofile, 'this is com5', com3,
            create_new_objects)
    com6 = create_comment(bob_userprofile, 'this is com6', com5,
            create_new_objects)
    com7 = create_comment(ice_userprofile, 'this is com7', com1,
            create_new_objects)
    com8 = create_comment(ice_userprofile, 'this is com8', com2,
            create_new_objects)

    # make a client available to use
    client = Client()

    # make paginator available to use
    paginator = Paginator(NewsItem.objects.all(), 15)



if __name__ == '__main__':
    base.main(setup_path_and_args, init_db, usage)

    # import all of this so I can use it easily with IPython
    from news.models import UserProfile, NewsItem, Comment, \
            Rated, Rankable
    from django.contrib.auth.models import User 
    from news.helpers import get_child_comments, get_next_with_pages, \
            get_pagenum, get_paginator_page, datetime_ago, improve_url, assert_or_404
    from news.shortcuts import get_object_or_404, \
        get_from_POST_or_404, get_from_session
    from news.validation import valid_comment_text, valid_email, \
            valid_next_redirect, valid_password, valid_text, \
            valid_title, valid_url, valid_username 

    from django.contrib.sessions.backends.db import SessionStore
    from django.contrib.sessions.models import Session
    from django.http import HttpResponseRedirect
    from django.shortcuts import render_to_response
    from django.core.urlresolvers import reverse, resolve
    from django.template import RequestContext
    from django.conf import settings
    from django.core.paginator import Paginator, InvalidPage, EmptyPage
    from django.test.client import Client
    from django.test import TestCase

    from urlparse import urlparse
    from urllib import urlencode
    import random
