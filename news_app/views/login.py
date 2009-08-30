"""
Views dealing with logging in and out and creating users.
"""
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.template import RequestContext

from news.models import UserProfile
from django.contrib.auth.models import User
from news.shortcuts import get_from_session, get_from_POST_or_404 
from news.helpers import assert_or_404
from news.validation import valid_next_redirect, valid_username, \
        valid_password


def logout_view(request):
    """
    Log out a user.  (It doesn't matter if they are logged in or not...)

    Takes GET requests.
    """
    next = request.GET.get('next', reverse('news.views.news_items.index'))
    assert_or_404(valid_next_redirect(next))

    logout(request)
    return HttpResponseRedirect(next)

def login_view(request):
    """
    Perform login or show login page.

    On GETs it shows the login page, 
    on POSTS it tries to log the user in.
    """
    # If next is passed, get it.
    # I am only attempting to get it from POST so I can use it in testing.
    next = request.GET.get('next', reverse('news.views.news_items.index'))
    next = request.POST.get('next', next)
    assert_or_404(valid_next_redirect(next))

    if request.method != 'POST':
        # if there is a login error or create account error 
        # in session, get the value
        login_error = get_from_session(request, "login_error")
        username = get_from_session(request, "login_username")
        create_account_error = get_from_session(request, 
                "create_account_error")
        create_account_username = get_from_session(request, 
                "create_account_username")
        return render_to_response('news/login.html',
                {'login_error': login_error, 
                 'username': username,
                 'create_account_error': create_account_error,
                 'create_account_username': create_account_username,
                 'next': next},
                context_instance=RequestContext(request))

    username = get_from_POST_or_404(request, 'username')
    password = get_from_POST_or_404(request, 'password')
    user = authenticate(username=username, password=password)

    if user is None:
        request.session['login_error'] = "Invalid username or password"
        request.session['login_username'] = username
        return HttpResponseRedirect(reverse('news.views.login.login_view') +
                "?next=" + next)
    if not user.is_active:
        request.session['login_error'] = "Account disabled"
        request.session['login_username'] = username
        return HttpResponseRedirect(reverse('news.views.login.login_view') +
                "?next=" + next)

    # before we login the user, makes sure to get their session variables,
    # and put them back into the session after calling login().
    # login() will flush everything, so we need to make sure to save the stuff
    # we want.  This is used when the user trys to post 
    # a comment if they are not logged in.  We will reload 
    # the page and send them back to the page with their comment
    # already filled in.
    comment_text = get_from_session(request, 'comment_text')
    comment_text_for_id = get_from_session(request, 'comment_text_for_id')

    submit_title = get_from_session(request, 'submit_title')
    submit_url = get_from_session(request, 'submit_url')
    submit_text = get_from_session(request, 'submit_text')

    # user has be authenticated and they are active
    login(request, user)

    request.session['comment_text'] = comment_text
    request.session['comment_text_for_id'] = comment_text_for_id

    request.session['submit_title'] = submit_title
    request.session['submit_url'] = submit_url
    request.session['submit_text'] = submit_text

    return HttpResponseRedirect(next)

def create_account(request):
    """
    Respond to posts for creating an account.

    Only takes POSTs.
    """
    # if next is passed, get it
    next = request.GET.get('next', reverse('news.views.news_items.index'))
    next = request.POST.get('next', next)
    assert_or_404(valid_next_redirect(next))

    assert_or_404(request.method == 'POST')

    username = get_from_POST_or_404(request, 'username')
    password = get_from_POST_or_404(request, 'password')

    # make sure it's a valid username
    if not valid_username(username):
        request.session['create_account_error'] = 'Username can only ' + \
            'consist of letters, numbers, and underscores, and must be ' + \
            'less than 30 characters'
        request.session['create_account_username'] = username
        return HttpResponseRedirect(reverse('news.views.login.login_view') +
                "?next=" + next)

    # make sure no other users have this username
    if User.objects.filter(username=username):
        request.session['create_account_error'] = \
                'Username ' + username + ' taken'
        request.session['create_account_username'] = username
        return HttpResponseRedirect(reverse('news.views.login.login_view') +
                "?next=" + next)

    # make sure it's a valid password
    if not valid_password(password):
        request.session['create_account_error'] = \
                 'Password cannot be blank and must be less than 30 characters'
        request.session['create_account_username'] = username
        return HttpResponseRedirect(reverse('news.views.login.login_view') +
                "?next=" + next)

    # create the user and userprofile
    user = User.objects.create_user(username, '', password)
    UserProfile.objects.create(user=user)

    return login_view(request)


def change_password(request):
    """
    Change password.

    On GETs it shows the change password page.
    On POSTs it tries to change the user's password.
    """
    next = reverse('news.views.login.change_password')

    if not request.user.is_authenticated():
        return HttpResponseRedirect(
                reverse('news.views.login.login_view') +
                '?next=' + next)

    if request.method != 'POST':
        change_password_error = get_from_session(request, 
                'change_password_error')
        return render_to_response('news/change_password.html',
                {'change_password_error': change_password_error,
                 'next': next},
                context_instance=RequestContext(request))

    password1 = get_from_POST_or_404(request, 'password1')
    password2 = get_from_POST_or_404(request, 'password2')

    if password1 != password2:
        request.session['change_password_error'] = "Passwords do not match"
        return HttpResponseRedirect(reverse('news.views.login.change_password'))

    if not valid_password(password1):
        request.session['change_password_error'] = "Password too long or blank"
        return HttpResponseRedirect(reverse('news.views.login.change_password'))
    

    request.user.set_password(password1)
    request.user.save()

    username = request.user.username

    return HttpResponseRedirect(reverse('news.views.users.user', args=(username,)))


