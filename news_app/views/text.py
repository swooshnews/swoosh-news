"""
Serve pages that are mostly text.  
This file doesn't do anything that exciting.
"""
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext

def about(request):
    """
    About Page
    """
    next = reverse('news.views.text.about')

    return render_to_response('news/about.html',
            {'next': next,},
            context_instance=RequestContext(request))

def guidelines(request):
    """
    Guidelines Page
    """
    next = reverse('news.views.text.guidelines')

    return render_to_response('news/guidelines.html',
            {'next': next,},
            context_instance=RequestContext(request))

def faq(request):
    """
    FAQ Page
    """
    next = reverse('news.views.text.faq')

    return render_to_response('news/faq.html',
            {'next': next,},
            context_instance=RequestContext(request))

def bookmarklet(request):
    """
    bookmarklet Page
    """
    next = reverse('news.views.text.bookmarklet')

    return render_to_response('news/bookmarklet.html',
            {'next': next,},
            context_instance=RequestContext(request))

def price(request):
    """
    Price page for posting and voting 
    """
    next = reverse('news.views.text.price')

    return render_to_response('news/price.html',
            {'next': next,},
            context_instance=RequestContext(request))
