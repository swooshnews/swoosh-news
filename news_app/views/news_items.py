"""
These are views that have something to do with news items.
"""

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext

import news.conf as news_settings

from news.models import NewsItem, Rated
from news.helpers import datetime_ago, get_child_comments, \
        improve_url, get_pagenum, get_paginator_page, \
        get_next_with_pages, get_frontpage_querymanager
from news.validation import valid_text, valid_title, valid_url
from news.shortcuts import get_object_or_404, get_from_POST_or_404, \
        get_from_session, get_from_GET_or_404

import datetime
import urllib


def index(request):
    """
    View for the front page.

    Only responds to GET requests.
    """
    render_start = datetime.datetime.now()

    querymanager = get_frontpage_querymanager(request)
    page = get_pagenum(request)
    front_page = get_paginator_page(querymanager, page)

    header = 'Front Page'

    next = get_next_with_pages(reverse('news.views.news_items.index'), page)
    this = reverse('news.views.news_items.index')

    render_end = datetime.datetime.now()

    return render_to_response('news/news_item_list.html',
            {'news_item_list': front_page.object_list,
             'paginator_page': front_page,
             'header': header,
             #'render_time': render_end - render_start,
             'next': next,
             'this': this},
            context_instance=RequestContext(request))


def new_news_items(request):
    """
    View for the new news items.

    Only responds to GET requests.
    """

    if request.user.is_authenticated() and request.user.get_profile().option_show_dead:
        querymanager = NewsItem.objects.all().order_by('-date_posted')
    else:
        querymanager = NewsItem.objects.filter(dead=False).order_by('-date_posted')

    page = get_pagenum(request)
    latest_page = get_paginator_page(querymanager, page)

    header = 'New'

    this = reverse('news.views.news_items.new_news_items')
    next = get_next_with_pages(reverse('news.views.news_items.new_news_items'), page)

    return render_to_response('news/news_item_list.html',
            {'news_item_list': latest_page.object_list,
             'paginator_page': latest_page,
             'header': header,
             'next': next,
             'this': this},
            context_instance=RequestContext(request))


def news_item(request, news_item_id=None):
    """
    View for a news item.

    Only responds to GET requests.
    """
    top_news_item = get_object_or_404(NewsItem, pk=news_item_id)
    child_comments = get_child_comments(top_news_item.child_set, 0)

    header = 'News Item'

    # these are only set if there is an error or something
    comment_posting_error = get_from_session(request, 'comment_posting_error')
    comment_text = get_from_session(request, 'comment_text')
    comment_text_for_id = get_from_session(request, 'comment_text_for_id')

    # comment_text_for_id needs to be a string
    if str(comment_text_for_id) != news_item_id:
        comment_text = ''
        comment_posting_error = ''

    next = reverse('news.views.news_items.news_item', 
                   args=(top_news_item.id,))

    top_news_item.update_ranking()

    return render_to_response('news/news_item.html',
            {'top_news_item': top_news_item,
             'child_comments': child_comments,
             'header': header,
             'comment_posting_error':comment_posting_error,
             'comment_text': comment_text,
             'next': next},
            context_instance=RequestContext(request))


def submit(request):
    """
    View for submitting an item.

    On GET it shows the page for submitting news items.
    Some of the data can be filled in from parameters
    passed in from the URL.

    On POST it tries to submit a news item.
    """
    next = reverse('news.views.news_items.submit')

    if request.method != 'POST':
        title = ''
        url = ''
        text = ''
        submission_error = ''
        if 'submit_title' in request.session:
            title = get_from_session(request, 'submit_title')
            url = get_from_session(request, 'submit_url')
            text = get_from_session(request, 'submit_text')
            submission_error = get_from_session(request, 'submission_error')
        # this enables submission by bookmarklet
        elif 'title' in request.GET:
            title = request.GET.get('title', '')
            url = request.GET.get('url', '')
            url = urllib.unquote(url)
        return render_to_response('news/submit.html',
                {'title': title,
                 'url': url,
                 'text': text,
                 'submission_error': submission_error,
                 'next': next},
                context_instance=RequestContext(request))

    title = get_from_POST_or_404(request, 'title')
    url = get_from_POST_or_404(request, 'url')
    text = get_from_POST_or_404(request, 'text')

     
    url = improve_url(url)
    
    submission_error = check_submission(title, url, text)


    if submission_error:
        request.session['submit_title'] = title
        request.session['submit_url'] = url
        request.session['submit_text'] = text
        request.session['submission_error'] = submission_error 
        return HttpResponseRedirect(reverse('news.views.news_items.submit'))

    if not request.user.is_authenticated():
        request.session['submit_title'] = title
        request.session['submit_url'] = url
        request.session['submit_text'] = text
        
        return HttpResponseRedirect(
                    reverse('news.views.login.login_view') +
                    '?next=' + next)

    # if the url has already been posted, just vote up this story
    if url and NewsItem.objects.filter(url=url):
        newsitem = NewsItem.objects.filter(url=url)[0]
        news_item_next = reverse('news.views.news_items.news_item', 
                            args=(newsitem.id,))
        vote_next = reverse('news.views.voting.vote') + '?' + \
            urllib.urlencode({'id': newsitem.id, 
                              'type': 'news_item',
                              'direction': 'up',
                              'next': news_item_next})

        return HttpResponseRedirect(vote_next)


    
    # now we can create the news item
    newsitem = NewsItem.objects.create(poster=request.user.get_profile(),
                            title=title, url=url, text=text)
    Rated.objects.create(rankable=newsitem, userprofile=request.user.get_profile(), 
                            direction='up')

    return HttpResponseRedirect(
            reverse('news.views.news_items.news_item', 
                    args=(newsitem.id,)))

    


def check_submission(title, url, text):
    """
    This will check a submission for errors and return
    a string containing the first error found, or '' 
    if there are no errors.
    """
    if not valid_title(title):
        return 'Title must be between 1 and ' +  \
                str(news_settings.NEWS_MAX_TITLE_LENGTH) + ' characters'

    if not url and not text:
        return 'Enter url or text'

    if url and text:
        return 'Only url OR text (not both)'

    if url and not valid_url(url):
        return 'URL not valid'

    if text and not valid_text(text):
        return 'Text not valid'

    # no error
    return ''



