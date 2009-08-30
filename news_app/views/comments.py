"""
These are views that deal with comments.  That is, 
new comments, a comment view, and a POST-only view
that deals with submitting comments.
"""
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext

from news.models import NewsItem, Comment, Rated, Rankable
from news.helpers import get_child_comments, assert_or_404, \
    get_paginator_page, get_pagenum, get_next_with_pages
from news.validation import valid_comment_text, valid_next_redirect
from news.shortcuts import get_object_or_404, \
    get_from_POST_or_404, get_from_session, del_from_session


def new_comments(request):
    """
    View for the new comments.

    Only responds to GETs.
    """
    querymanager = Comment.objects.filter(dead=False).order_by('-date_posted')
    page = get_pagenum(request)
    latest_page = get_paginator_page(querymanager, page)

    header = 'New Comments'

    this = reverse('news.views.comments.new_comments')
    next = get_next_with_pages(reverse('news.views.comments.new_comments'), page)

    return render_to_response('news/comment_list.html',
            {'latest_comments': latest_page.object_list,
             'paginator_page': latest_page,
             'header': header,
             'next': next,
             'this': this},
            context_instance=RequestContext(request))


def comment(request, comment_id):
    """
    View for a comment.

    Only responds to GETS.
    """
    top_comment = get_object_or_404(Comment, pk=comment_id)
    child_comments = get_child_comments(top_comment.child_set, 0)

    header = 'Comment'


    # these are set if there is an error or something when trying to post
    # the comment
    comment_posting_error = get_from_session(request, 'comment_posting_error')
    comment_text = get_from_session(request, 'comment_text')
    comment_text_for_id = get_from_session(request, 'comment_text_for_id')

    # comment_text_for_id needs to be a string
    if str(comment_text_for_id) != comment_id:
        comment_posting_error = ''
        comment_text = ''

    next = reverse('news.views.comments.comment', 
                   args=(top_comment.id,))

    top_comment.update_ranking()

    return render_to_response('news/comment.html',
            {'top_comment': top_comment,
             'child_comments': child_comments,
             'header': header,
             'comment_posting_error': comment_posting_error,
             'comment_text': comment_text,
             'next': next},
            context_instance=RequestContext(request))


def submit_comment(request):
    """
    View for submitting a comment.
    
    If the user is not authenticated, we set the session variables
    'comment_text', and 'comment_text_for_id'. We then send the
    user to the login page.  When the user is directed back to their
    previous comment view or news item view, these session variables
    are read and inserted into the view.

    Only takes POSTs.
    """
    assert_or_404(request.method == 'POST')

    parent_id = get_from_POST_or_404(request, 'parent_id')
    parent = get_object_or_404(Rankable, id=parent_id)

    comment_text = get_from_POST_or_404(request, 'comment_text')

    # if a comment matches the parent id, that means we
    # are responding to a comment. If a news item matches the 
    # comment id, that means we are responding to a news item.
    # We figure this out now because we use it a bunch later.
    if Comment.objects.filter(id=parent.id):
        next = reverse('news.views.comments.comment', args=(parent_id,))
    else:
        next = reverse('news.views.news_items.news_item', args=(parent_id,))


    if not valid_comment_text(comment_text):
        request.session['comment_posting_error'] = "Comment not valid"
        request.session['comment_text_for_id'] = parent.id
        return HttpResponseRedirect(next)
        

    # if the user is not authenticated, send them to login,
    # (and set some session variables so they don't lose the comment they posted)
    if not request.user.is_authenticated():
        request.session['comment_text'] = comment_text
        request.session['comment_text_for_id'] = parent.id
        return HttpResponseRedirect(reverse('news.views.login.login_view') +
                        '?next=' + next)

    # if the user doesn't have enough comment points to post,
    # return them to this page and show them an error.
    if not parent.can_post_comment(request.user.get_profile()):
        request.session['comment_posting_error'] = "Insufficient comment points"
        request.session['comment_text_for_id'] = parent.id
        request.session['comment_text'] = comment_text
        return HttpResponseRedirect(next)


    userprofile = request.user.get_profile()

    # post comment  
    com = Comment.objects.create(poster=userprofile,
            text=comment_text, parent=parent)
    Rated.objects.create(rankable=com, userprofile=userprofile, 
                            direction='up')
    userprofile.comment_points -= com.comment_cost(userprofile)
    userprofile.save()


    # I don't think this is needed, because these keys should already
    # be taken out of session when they are read (we only set them on error), 
    # but just to make sure we clear them here.
    del_from_session(request, 'comment_text')
    del_from_session(request, 'comment_text_for')
    del_from_session(request, 'comment_text_for_id')
    

    # if there is a parent, return the comment view for that parent
    return HttpResponseRedirect(next)

def edit_comment(request, comment_id):
    """
    View for editing a comment.

    Responds to GET and POST.  Get for getting the view and POST
    for updating the comment.
    """
    com = get_object_or_404(Comment, pk=comment_id)

    next = reverse('news.views.comments.edit_comment', 
                   args=(com.id,))

    # This calculates the page we came from.
    # If it is not given, it just defaults to the 
    # news item (if that's what is being deleted),
    # or the parent news item of the comment that
    # is being deleted.
    top_news_item = com.get_parent_news_item()
    from_page = request.GET.get('from', 
            reverse('news.views.news_items.news_item', 
                args=(top_news_item.id,)))
    assert_or_404(valid_next_redirect(from_page))

    # you should not be able to see this page or edit any comment
    # if you are not logged in or if you are trying to edit someone
    # else's comment
    assert_or_404(request.user.is_authenticated() and \
           com.can_be_edited(request.user.get_profile()))

    # make sure the item hasn't already been deleted.
    assert_or_404(not com.dead)

    # on GET we can just return the template
    if request.method != "POST":
        comment_posting_error = get_from_session(request, 'comment_posting_error')
        comment_text = get_from_session(request, 'comment_text')
        return render_to_response('news/edit_comment.html',
                {'comment_posting_error': comment_posting_error,
                 'comment': com,
                 # this will default to comment_text but if it is blank it
                 # looks at com.text
                 'comment_text': comment_text or com.text,
                 'from_page': from_page,
                 'next': next},
                context_instance=RequestContext(request))

    comment_text = get_from_POST_or_404(request, 'comment_text')

    # if it is not valid, set the error message 
    # and reload this page
    if not valid_comment_text(comment_text):
        request.session['comment_posting_error'] = "Comment not valid"
        request.session['comment_text'] = comment_text
        return HttpResponseRedirect(next)

    com.text = comment_text
    com.save()

    return HttpResponseRedirect(from_page)

