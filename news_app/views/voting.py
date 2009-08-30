"""
Views for dealing with voting (rating comments and news items).
"""
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse

from news.models import NewsItem, Comment, Rated, Rankable
from news.helpers import assert_or_404
from news.validation import valid_next_redirect
from news.shortcuts import get_object_or_404, \
    get_from_GET_or_404 


def vote(request):
    """
    This view takes a vote for a comment or news item.
    It then redirects back to said comment or news item.

    It only takes GET requests.
    """
    rankable_id = get_from_GET_or_404(request, 'id')
    direction = get_from_GET_or_404(request, 'direction')
    next = get_from_GET_or_404(request, 'next')

    assert_or_404(direction == 'up' or direction == 'down')
    assert_or_404(valid_next_redirect(next))

    rankable = get_object_or_404(Rankable, id=rankable_id)

    if not request.user.is_authenticated():
        # TODO: this next should actually be redirecting back to this vote view,
        # which then redirects to whatever the previous view was, so, two levels
        # of redirection.
        return HttpResponseRedirect(
                reverse('news.views.login.login_view') +
                '?next=' + next)
    
    userprofile = request.user.get_profile()

    if rankable.already_voted(userprofile):
        return HttpResponseRedirect(next)

    if not rankable.can_vote(userprofile):
        request.session['voting_error'] = "Not enough comment points"
        return HttpResponseRedirect(reverse('news.views.payment.buy_points'))


    if direction == 'up':
        rankable.rating += 1
    elif direction == 'down':
        assert_or_404(rankable.can_be_downvoted())
        rankable.rating -= 1
    else:
        raise Http404

    rankable.update_ranking()
    rankable.save()
    Rated.objects.create(rankable=rankable, userprofile=userprofile, 
                            direction=direction)

    userprofile.comment_points -= rankable.vote_cost(userprofile)
    userprofile.save()


    return HttpResponseRedirect(next)


