"""
Views operating on rankables in general, not just comments or news items.
"""

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext

from news.models import NewsItem, Comment, Rated, Rankable
from news.helpers import assert_or_404
from news.shortcuts import get_object_or_404, \
    get_from_POST_or_404, get_from_session, del_from_session
from news.validation import valid_next_redirect


def delete_rankable(request, rankable_id):
    """
    View for deleting a news item or comment.

    Responds to GET and POST.  GET for getting the template and POST
    for actually doing the deleting.
    """
    rankable = get_object_or_404(Rankable, pk=rankable_id)

    next = reverse('news.views.rankables.delete_rankable', 
                   args=(rankable.id,))

    # This calculates the page we came from.
    # If it is not given, it just defaults to the 
    # news item (if that's what is being deleted),
    # or the parent news item of the comment that
    # is being deleted.
    top_news_item = rankable.get_parent_news_item()
    from_page = request.GET.get('from', 
            reverse('news.views.news_items.news_item', 
                args=(top_news_item.id,)))
    assert_or_404(valid_next_redirect(from_page))

    # you should not be able to see this page or edit any comment
    # if you are not logged in or if you are trying to edit someone
    # else's comment
    assert_or_404(request.user.is_authenticated() and \
            rankable.can_be_deleted(request.user.get_profile()))

    # this must be a comment or a news item
    assert_or_404(rankable.is_comment() or rankable.is_news_item())

    # make sure the item hasn't already been deleted.
    assert_or_404(not rankable.dead)

    # on GET we can just return the template
    if request.method != "POST":
        news_item = None
        comment = None
        if rankable.is_comment():
            comment = rankable.comment
        elif rankable.is_news_item():
            news_item = rankable.newsitem
        return render_to_response('news/delete_rankable.html',
                {'news_item': news_item,
                 'comment': comment,
                 'rankable': rankable,
                 'from_page': from_page,
                 'next': next},
                context_instance=RequestContext(request))


    # this should either be "yes" or "no"
    submitvalue = get_from_POST_or_404(request, 'submitvalue')

    if submitvalue == "yes":
        rankable.dead = True
        rankable.save()

    return HttpResponseRedirect(from_page)
