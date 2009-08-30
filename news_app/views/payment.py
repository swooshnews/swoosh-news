"""
Handle all payment functions.
"""

from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from news.shortcuts import get_from_session

import news.conf

def buy_points(request):
    """
    Throw up a template for making a payment on an account.
    Must be logged in.
    """
    next = reverse('news.views.payment.buy_points')

    # make sure user is authenticated
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('news.views.login.login_view') +
                '?next=' + next)

    voting_error = get_from_session(request, 'voting_error')
    return render_to_response('news/buy_points.html',
            {'next': next,
             'voting_error': voting_error,},
            context_instance=RequestContext(request))

def cancel(request):
    """
    The user was taken to paypal but cancelled their payment.
    """
    next = reverse('news.views.payment.cancel')
    return render_to_response('news/cancel.html',
            {'next': next,},
            context_instance=RequestContext(request))

def success(request):
    """
    The user was taken to paypal, paid, and returned here.
    """
    next = reverse('news.views.payment.success')
    return render_to_response('news/success.html',
            {'next': next,},
            context_instance=RequestContext(request))

