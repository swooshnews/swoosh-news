"""
These are models for news that are in the database.
"""
from django.db import models
from django.contrib.auth.models import User

import news.conf as news_settings

# This is used to set up the signals and callbacks for this app.
# The signal stuff needs to get imported early on, so it should go here.
import news.signals 

import datetime
from urlparse import urlparse



class UserProfile(models.Model):
    """
    This is a profile to a user.  It is intrinsically
    linked to django's default User model.  This UserProfile
    holds additional info about the user.
    """
    # a link to the user's website
    website = models.URLField(default="", verify_exists=False, 
            max_length=news_settings.NEWS_MAX_URL_LENGTH)
    # the remaining comment points
    comment_points = models.IntegerField(default=0)
    user = models.ForeignKey(User, unique=True)
    date_created = models.DateTimeField(default=datetime.datetime.now)
    # the about box on the user's profile page
    about = models.TextField(default="")
    option_show_email = models.BooleanField(default=False)
    option_use_javascript = models.BooleanField(default=False)
    option_show_dead = models.BooleanField(default=False)

    # log user's ip address
    created_from_ip = models.IPAddressField(null=True)
    last_login_ip = models.IPAddressField(null=True)

    def __unicode__(self):
        return self.user.username

    def _get_username(self):
        return self.user.username
    username = property(_get_username)


class Rated(models.Model):
    """
    This is the manager for the ManyToManyField
    holding the person who rates the Rankable object.
    """
    DIRECTION_CHOICES = (('up', 'Up'), ('down', 'Down'))

    rankable = models.ForeignKey('Rankable')
    userprofile = models.ForeignKey(UserProfile)
    date_rated = models.DateTimeField(default=datetime.datetime.now)
    direction = models.CharField(max_length=4, choices=DIRECTION_CHOICES)
    ranked_from_ip = models.IPAddressField(null=True)

class Rankable(models.Model):
    """
    This is anything that can be ranked (i.e., have a rating).
    Mainly this is just for Comment and NewsItem.
    """
    poster = models.ForeignKey(UserProfile)
    date_posted = models.DateTimeField(default=datetime.datetime.now)

    # if a rankable has been deleted
    dead = models.BooleanField(default=False)

    # http://www.djangoproject.com/documentation/models/many_to_many/
    raters = models.ManyToManyField(UserProfile, related_name="rated_%(class)ss",
            through='Rated')
    
    # the rating for the field (if someone up votes this Rankable,
    # the rating will go up by one)
    rating = models.IntegerField(default=1)

    # the ranking, which is calculated by the function below
    ranking = models.FloatField(default=0)

    last_ranked_date = models.DateTimeField(default=datetime.datetime.now)

    posted_from_ip = models.IPAddressField(null=True)

    def calculate_ranking(self):
        """
        Easy algorithm:
        http://www.seomoz.org/blog/reddit-stumbleupon-delicious-and-hacker-news-algorithms-exposed
        More complicated algorithm:
        http://arcfn.com/2009/06/how-does-newsyc-ranking-work.html
        """
        delta = datetime.datetime.now() - self.date_posted
        hours = (delta.days * 24.0) + (delta.seconds / 3600.0)
        # simpler way
        return (self.rating - 1.0) / ((hours + 2.0) ** 1.5)
        # more compllicated way
        # return ((rating - 1.0) ** .8) / ((hours + 2.0) ** 1.8)

    def update_ranking(self):
        """
        Update the ranking for the Rankable.
        The rankable is saved to the database after updating.
        """
        self.ranking = self.calculate_ranking()
        self.last_ranked_date = datetime.datetime.now()
        # TODO: should this save?
        self.save()

    def is_news_item(self):
        """Returns true if this rankable is a news item."""
        if NewsItem.objects.filter(id=self.id):
            return True
        else:
            return False

    def is_comment(self):
        """Returns true if this rankable is a comment."""
        if Comment.objects.filter(id=self.id):
            return True
        else:
            return False

    def __unicode__(self):
        uni_string = "" 
        if self.is_news_item():
            uni_string += "NewsItem: " + unicode(self.newsitem)
        elif self.is_comment():
            uni_string += "Comment: " + unicode(self.comment)
        else:
            uni_string += "id " + unicode(self.id)
        return uni_string

    def num_child_comments(self):
        """
        This returns the number of comments a news item (or a comment) has
        """
        if hasattr(self, 'child_set'):
            from news.helpers import get_child_comments
            return len(get_child_comments(self.child_set, return_dead=False))
        else:
            return 0

    def has_children(self):
        """
        This returns wheter or not a news item (or comment) has children.
        """
        if hasattr(self, 'child_set'):
            from news.helpers import get_child_comments
            return len(get_child_comments(self.child_set)) > 0
        else:
            return False

    def has_nondead_children(self):
        """
        This returns wheter or not a news item (or comment) has children and
        at least one of them is not dead.
        """
        if hasattr(self, 'child_set'):
            from news.helpers import get_child_comments
            return len(get_child_comments(self.child_set, return_dead=False)) > 0
        else:
            return False

    def can_be_edited(self, userprofile):
        """ Return whether the given userprofile can edit a rankable. """
        from news.helpers import datetime_ago
        if self.poster == userprofile and \
                self.date_posted > \
                datetime_ago(minutes=news_settings.NEWS_COMMENT_EDITABLE_MINS):
            return True
        return False

    def can_be_deleted(self, userprofile):
        """ Return whether the given userprofile can delete a rankable. """
        return self.can_be_edited(userprofile)

    def get_parent_news_item(self):
        """
        If this rankable is a news item, just return the 
        news item.  If this rankable is a comment,
        return the news item this comment is posted to.
        """
        if self.is_news_item():
            return self.newsitem
        elif self.is_comment():
            return self.comment.get_newsitem()
        else:
            return None

    def can_be_downvoted(self):
        """ Return true if this rankable can be down-voted. """
        if self.is_comment():
            return False
        else:
            return True

    def can_post_comment(self, userprofile):
        """ 
        Return True if userprofile can post a comment to this rankable.
        Checks to make sure whehter we are posting to a regular news item,
        or an "Ask SN:" news item. 
        """
        return userprofile.comment_points - \
                self.comment_cost(userprofile) >= 0

    def comment_cost(self, userprofile):
        """ 
        Calculate the cost of posting a comment.  It it different
        depending on whether we are posting to a regular news item,
        or to an "Ask SN:" item.
        """
        parent_news_item = self.get_parent_news_item()
        if parent_news_item:
            if parent_news_item.is_normal_news_item():
                return news_settings.NEWS_COST_RESPOND_NEWS_ITEM
            elif parent_news_item.is_ask_sn():
                return news_settings.NEWS_COST_RESPOND_ASK_SN
        return 0

    def can_vote(self, userprofile):
        """ 
        Return True if userprofile can vote on this rankable.
        This function makes sure that the user has enough comment_points.
        """
        return userprofile.comment_points - \
                self.vote_cost(userprofile) >= 0

    def vote_cost(self, userprofile):
        """ 
        Calculate the cost of voting a comment. It differs
        depending on what we are voting on.
        """
        if self.is_news_item():
            parent_news_item = self.get_parent_news_item()
            if parent_news_item.is_ask_sn():
                return news_settings.NEWS_COST_VOTE_ASK_SN
            elif parent_news_item.is_normal_news_item():
                return news_settings.NEWS_COST_VOTE_NEWS_ITEM

        if self.is_comment():
            parent_news_item = self.get_parent_news_item()
            if parent_news_item:
                if parent_news_item.is_normal_news_item():
                    return news_settings.NEWS_COST_VOTE_NORMAL_COMMENT
                elif parent_news_item.is_ask_sn():
                    return news_settings.NEWS_COST_VOTE_ASK_SN_COMMENT
        return 0


    def already_voted(self, userprofile):
        """ Returns True if userprofile already voted on this rankable. """
        return len(self.raters.filter(id=userprofile.id)) > 0


class NewsItem(Rankable):
    """
    A news item or an "Ask Swoosh News" item.  Not a comment.
    """
    # Every News item needs to be either a link to some other page
    # OR some text.
    title = models.CharField(max_length=news_settings.NEWS_MAX_TITLE_LENGTH)
    url = models.URLField(null=True, verify_exists=False, 
                          max_length=news_settings.NEWS_MAX_URL_LENGTH)
    text = models.TextField(null=True)

    def __unicode__(self):
        if self.url:
            return '%s (%s)' % (self.title, self.url)
        elif self.text:
            return '%s (%s)' % (self.title, self.text[0:20])
        else:
            return '%s (%s)' % (self.title, "ERROR! No URL or text!")

    def is_normal_news_item(self):
        """ 
        Returns true if this is a normal news item.  It's not a 
        text post, but a post with a URL.
        """
        if self.text:
            return False
        else:
            return True

    def is_ask_sn(self):
        """
        Returns true if this is an "Ask Swoosh News"-type news post.
        (no url to another site)
        """
        return not self.is_normal_news_item()

    def abbr_url(self):
        """
        Returns an abbreviated url with just the domain name and tld.
        """
        if not self.url:
            return ''
        (scheme, netloc, path, params, query, fragment) = urlparse(self.url)
        if netloc.startswith("www."):
            return netloc[4:]
        return netloc

    def response_cost(self):
        """ Cost for responding to this news item in comment points. """
        if self.is_normal_news_item():
            return news_settings.NEWS_COST_RESPOND_NEWS_ITEM
        elif self.is_ask_sn():
            return news_settings.NEWS_COST_RESPOND_ASK_SN
        else:
            return 0

class Comment(Rankable):
    """
    This represents a comment to a news item or a comment to a comment.
    """
    # the text for the comment
    text = models.TextField()

    parent = models.ForeignKey(Rankable, related_name='child_set')

    def get_newsitem(self):
        """ Get the newsitem that this is posted to."""
        if self.parent.is_news_item():
            return self.parent.newsitem
        else: 
            return self.parent.comment.get_newsitem()

    def __unicode__(self):
        return '%s ("%s")' % (self.poster.username, self.text[0:20])


