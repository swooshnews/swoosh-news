"""
This file eases some of the pain when calling scripts from the 
command line that must interact with a Django project or a Django app.

To use this file, you must create at least 2 functions: a setup function and
a main function.

The setup function should process the additional command line arguments.
The main function should accept the additional command line arguments as args,
and must do the main functionality.

Look at news/scripts/init_db_vals.py for an example.
"""

import sys, os, getopt

# these defaults are used in usage() and in main()
default_app_path = ''
default_project_path  = '' 
default_app_name  = '' 
default_project_name  = '' 

def usage(explanation, extra_commands):  
    global default_app_path 
    global default_project_path
    global default_app_name
    global default_project_name

    print "Usage: " + sys.argv[0] + " [OPTIONS]"
    for line in explanation:
        print line
    print
    print "    --app-name=NAME\t\tname of this app (should be 'news')"
    print "-a, --app-path=PATH\t\tpython path for this app"
    print "-h, --help\t\t\tshow this help text"
    print "-n, --project-name=NAME\t\tname of the project containing this app"
    print "-p, --project-path=PATH\t\tpython path for the project containing this app"
    for line in extra_commands:
        print line
    print
    print
    print "default app-path:\t" + default_app_path
    print "default project-path:\t" + default_project_path
    print "default app-name:\t" + default_app_name
    print "default project-name:\t" + default_project_name


def get_int_arg(arg, error_string, usage_func, must_be_pos=False):
    """
    This is just a helper function to make sure I can get an
    int out of one of the args to this program.  It is
    being used to get the integer argument to --extra-news-items
    and --extra-comments.

    arg is the argument we are parsing.  error_string is the
    string to print if there is an error.  usage_func is the 
    function to call if there is an error.  must_be_pos is a 
    boolean telling whether or not the argument must be a positive
    number (e.g. greater than zero).
    """
    try:
        arg_val = int(arg)
    except ValueError:
        print error_string
        print
        usage_func()
        sys.exit(2)

    # create a function depending on whether the number
    # can be 0 or not.
    if must_be_pos:
        compare_func = lambda x: x <= 0
    else:
        compare_func = lambda x: x < 0

    # use this compare function on our argument
    if compare_func(arg_val):
        print error_string
        print
        usage_func()
        sys.exit(2)

    return arg_val

def get_paths_options(extra_short_opts, extra_long_opts, usage_func):
    # we are assumming that this script is inside of the 
    # scripts directory inside of the news app.
    # the news app is assumed to be inside of the 
    # main django project.
    # So, the directory structure should look like this,
    # /some/path/MY_PROJECT/THIS_APP/scripts/init_db_vals.py
    # app-path should therefore be /some/path/MY_PROJECT/
    # and project-path should therefore be /some/path/
    app_path = os.path.abspath('../..')
    project_path = os.path.abspath('../../..')

    app_name = os.path.basename(os.path.abspath('..'))
    project_name = os.path.basename(os.path.abspath('../..'))


    # these defaults are used in usage()
    global default_app_path
    global default_project_path
    global default_app_name
    global default_project_name
    default_app_path = app_path
    default_project_path  = project_path 
    default_app_name  = app_name 
    default_project_name  = project_name 

    # get the arguments
    try:                                
        opts, args = getopt.getopt(sys.argv[1:], 
                "ha:p:n:" + extra_short_opts, 
                ["help", "app-path=", "project-path=", "app-name=", 
                 "project-name=",] + extra_long_opts)
    except getopt.GetoptError:
        usage_func()                         
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage_func()
            sys.exit()
        elif opt in ("--app-path", "-a"):
            app_path = arg
        elif opt in ("--project-path", "-p"):
            project_path = arg
        elif opt in ("--project-name", "-n"):
            project_name = arg
        elif opt in ("--app-name",):
            app_name = arg



    # putting the app on the path
    sys.path.append(app_path)

    # putting the project on the path
    sys.path.append(project_path)


    os.environ["DJANGO_SETTINGS_MODULE"] = project_name + ".settings"

    return opts



def main(setup_func, main_func, usage_func):
    """
    Run setup and main code.
    """
    # This raises import error if the app and project aren't on the python path
    # or if the project_name is not set correctly.
    try: 
        kwargs = setup_func()
        main_func(**kwargs)
    except ImportError:
        # If there is an error, then the paths aren't correct.
        # Let's try to change directory into the directory that 
        # this script is in (probably SOMETHING/news/scripts/)
        # and then call all of this again
        try:
            os.chdir(os.path.dirname(sys.argv[0]))
            kwargs = setup_func()
            main_func(**kwargs)
        except ImportError:
            # Okay, there is something wrong.
            # Throw the error message and let's get out of here.
            print "ERROR! The app and the project must be on the python path."
            print "ERROR! The project name must be set correctly."
            print
            print "This is your current python path:"
            print sys.path
            print
            usage_func()
            sys.exit(2)

