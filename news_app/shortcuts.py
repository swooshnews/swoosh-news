"""
These are my shortcuts.
"""

from django.http import Http404
from django.shortcuts import get_object_or_404 as django_get_object_or_404

def get_object_or_404(klass, *args, **kwargs):
    """
    My wrapper around django's get_object_or_404 that will 
    raise Http404 on a value error.
    This is useful for example when I do something like
    get_object_or_404(Comment, id='cat')
    """
    try:
        return django_get_object_or_404(klass, *args, **kwargs)
    except ValueError:
        raise Http404


def get_from_POST_or_404(request, post_key):
    """
    Return value of post_key from request.POST.
    Raises Http404 exception if the key is not found.
    """
    if post_key not in request.POST:
        raise Http404
    return request.POST[post_key]


def get_from_GET_or_404(request, get_key):
    """
    Return value of get_key from request.GET.
    Raises Http404 exception if the key is not found.
    """
    if get_key not in request.GET:
        raise Http404
    return request.GET[get_key]


def get_from_session(request, sesh_key, default=''):
    """
    Returns value of sesh_key from request.session, 
    or default if sesh_key is not found.
    """
    sesh_var = default
    
    if sesh_key in request.session:
        sesh_var = request.session[sesh_key]
        del request.session[sesh_key]

    return sesh_var


def del_from_session(request, sesh_key):
    """
    Delete sesh_key from the session.
    If it doesn't exist, don't do anything.
    """
    if sesh_key in request.session:
        del request.session[sesh_key]

