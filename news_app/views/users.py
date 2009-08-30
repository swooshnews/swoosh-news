"""
These are views related to users.
"""
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from news.models import UserProfile
from news.shortcuts import get_object_or_404, get_from_POST_or_404, \
        get_from_session
from news.helpers import assert_or_404, improve_url
from news.validation import valid_text, valid_email, valid_url


def user(request, username):
    """
    View for a user.

    On GET it shows the user profile (which is editable if 
    the user is logged in and looking at their own profile.)
    On POST it tries to update the user's profile.
    """

    userprofile = get_object_or_404(UserProfile, user__username=username)

    next = reverse('news.views.users.user', args=(userprofile.username,))

    if request.method != 'POST':
        posting_error = get_from_session(request, 'userprofile_posting_error')
        email_address = get_from_session(request, 'userprofile_email')
        website = get_from_session(request, 'userprofile_website')
        about = get_from_session(request, 'userprofile_about')
        return render_to_response('news/user.html',
                {'viewing_userprofile': userprofile,
                 'next': next,
                 'posting_error': posting_error,
                 'error_email': email_address,
                 'error_website': website,
                 'error_about': about},
                context_instance=RequestContext(request))


    # don't allow users to POST without being logged in.
    # Also make sure the the user trying to post is the
    # one that is logged in.
    assert_or_404(request.user.is_authenticated())
    assert_or_404(request.user == userprofile.user)


    email_address = get_from_POST_or_404(request, 'email_address')  
    website = get_from_POST_or_404(request, 'website')  
    about = get_from_POST_or_404(request, 'about')  
    option_show_email = request.POST.get('option_show_email', False)
    option_use_javascript = request.POST.get('option_use_javascript', False)
    option_show_dead = request.POST.get('option_show_dead', False)

    # there shouldn't be a problem with option_show_email
    # or option_use_javascript, or option_show_dead, 
    # so we can go ahead and set them
    if option_use_javascript == False:
        userprofile.option_use_javascript = False
    else:
        userprofile.option_use_javascript = True

    if option_show_email == False:
        userprofile.option_show_email = False
    else:
        userprofile.option_show_email = True

    if option_show_dead == False:
        userprofile.option_show_dead = False
    else:
        userprofile.option_show_dead = True
    
    userprofile.save()
    
    if email_address and not valid_email(email_address):
        request.session['userprofile_posting_error'] = "Email address too long"
        request.session['userprofile_email'] = email_address
        request.session['userprofile_website'] = website
        request.session['userprofile_about'] = about
        return HttpResponseRedirect(reverse('news.views.users.user',
            args=(userprofile.username,)))

    if website:
        website = improve_url(website)
        if not valid_url(website):
            request.session['userprofile_posting_error'] = "URL not valid"
            request.session['userprofile_email'] = email_address
            request.session['userprofile_website'] = website
            request.session['userprofile_about'] = about
            return HttpResponseRedirect(reverse('news.views.users.user',
                args=(userprofile.username,)))

    if about and not valid_text(about):
        request.session['userprofile_posting_error'] = "About not valid"
        request.session['userprofile_email'] = email_address
        request.session['userprofile_website'] = website
        request.session['userprofile_about'] = about
        return HttpResponseRedirect(reverse('news.views.users.user',
            args=(userprofile.username,)))


    userprofile.website = website
    userprofile.about = about
    userprofile.user.email = email_address

    userprofile.save()
    userprofile.user.save()

    return HttpResponseRedirect(
            reverse('news.views.users.user', args=(userprofile.username,)))

