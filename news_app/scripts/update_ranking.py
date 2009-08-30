#!/usr/bin/python
"""
This is used to update the ranking for objects that are ranked.
This includes comments and news items.
"""

import getopt, sys, traceback
import base

usage_explanation =["Constantly update the ranking for objects that are ranked."]
usage_commands = ["-s, --milliseconds=N\t\tupdate a rankable every N milliseconds", 
                  "-d, --daemonize\t\trun the process in the background",]


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
    milliseconds = 500
    daemonize = False
    

    opts = base.get_paths_options("s:d", ["milliseconds=", "daemonize"], usage)

    for opt, arg in opts:
        if opt in ("--milliseconds", "-s"):
            milliseconds = base.get_int_arg(arg,
                    "ERROR! Argument to --milliseconds must be a positive integer.",
                    usage, must_be_pos=True)
        elif opt in ("-d", "--daemonize"):
            daemonize = True

    return {'milliseconds':milliseconds, 'daemonize':daemonize}


def update_ranking(milliseconds=500, daemonize=False):
    """ Update a random rankable every arg milliseconds.  """
    from random import randint
    import time
    import os, sys, fcntl
    from news.models import Rankable
    from news.helpers import get_frontpage_querymanager
    from news.conf import NEWS_UPDATE_RANKING_LOCKFILE


    # if this is a daemon, make sure it can only be run once
    try:
        fp = open(NEWS_UPDATE_RANKING_LOCKFILE, 'w')
    except IOError:
        print >>sys.stderr, "Error! Could not open lockfile " + NEWS_UPDATE_RANKING_LOCKFILE
        sys.exit(1)

    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print >>sys.stderr, "Error! Could not lock lockfile " + NEWS_UPDATE_RANKING_LOCKFILE
        sys.exit(1)


    if daemonize:
        if os.fork() == 0:
            # This is what the child does.
            #
            # I might need to call os.setsid() to set the
            # session id, so that this doesn't get exited
            # if I close the controlling terminal. Just 
            # like the code below.
            #
            #os.setsid()
            #if os.fork() == 0:
            #   pass
            #else:
            #   os._exit(0)
            pass
        else:
            # This is what the parent does.
            os._exit(0)

    # trying to see if I could call this from another process to get the
    # correct name
    #import sys
    #sys.argv[0] = "news name"
    #print "sys.argv = " + str(sys.argv)
    #print "__name__ = " + __name__


    def do_update(rankable):
        """ Do the update and pause for the set time. """
        rankable.update_ranking()
        if not daemonize:
            print >>sys.stderr, "Updated " + unicode(rankable)
        time.sleep(milliseconds / float(1000))

    def do_random_update_from_query(querymanager):
        """ Update a random rankable within querymanager. """
        num_rankables = querymanager.count()
        random_rankable = querymanager[randint(0, num_rankables-1)]
        do_update(random_rankable)


    while True:
        try:
            # update a random rankable
            do_random_update_from_query(Rankable.objects.all())

            # update least recently ranked rankable
            old_rankable = Rankable.objects.all().order_by('last_ranked_date')[0]
            do_update(old_rankable)

            # update random top 50 frontpage rankable
            do_random_update_from_query(get_frontpage_querymanager())

        except KeyboardInterrupt:
            # exit gracefully on ctrl-c
            if not daemonize:
                print >>sys.stderr, ""
            sys.exit(0)

        except:
            # Print stack trace and just keep going for any other type of exception
            if not daemonize:
                print >>sys.stderr, "\nException in update_ranking.py:"
                print >>sys.stderr, '-'*60
                traceback.print_exc(file=sys.stderr)
                print >>sys.stderr, '-'*60



if __name__ == '__main__':
    base.main(setup_path_and_args, update_ranking, usage)
