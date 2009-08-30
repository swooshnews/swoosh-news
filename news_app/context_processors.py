"""
Custom context processors for my templates.
"""
from django.conf import settings as django_settings
import news.conf as my_settings

def settings(request):
    """
    This context processor enables templates to use the settings variable.
    """
    all_settings = django_settings

    for item in my_settings.__dict__:
        if item.startswith("NEWS_"):
            all_settings.__setattr__(item, my_settings.__dict__[item])

    return {'settings': all_settings}

#############
##### use user.get_profile instead
#############
#def userprofile(request):
#   """
#   Templates get the userprofile variable.
#   """
#   import sys
#   print >>sys.stderr, "hasattr(request, 'user') = " + str(hasattr(request, 'user'))
#
#   if not hasattr(request, 'user'):
#       return {}
#
#   user = request.user
#
#   if user.userprofile_set.count() != 1:
#       return {}
#   else:
#       return {'userprofile': user.userprofile_set.all()[0]}


