"""
Django settings for the news app.
"""

from django.conf import settings

# max length for a news item title
NEWS_MAX_TITLE_LENGTH = getattr(settings, "NEWS_MAX_TITLE_LENGTH", 100)

# max length for a url
NEWS_MAX_URL_LENGTH = getattr(settings, "NEWS_MAX_URL_LENGTH", 125)

# max length for someone's email address
NEWS_MAX_EMAIL_LENGTH = getattr(settings, "NEWS_MAX_EMAIL_LENGTH", 100)

# This should be really high.  It is used
# for text length from comments and the 
# about field for the user page.
NEWS_MAX_TEXT_LENGTH = getattr(settings, "NEWS_MAX_TEXT_LENGTH", 100000)

# I wish I could pull this from django.contrib.auth.models.User 
NEWS_MAX_USERNAME_LENGTH = getattr(settings, "NEWS_MAX_USERNAME_LENGTH", 30)
NEWS_MAX_PASSWORD_LENGTH = getattr(settings, "NEWS_MAX_PASSWORD_LENGTH", 30)


# comments should be editable 60 minutes after they are posted
NEWS_COMMENT_EDITABLE_MINS = getattr(settings, "NEWS_COMMENT_EDITABLE_MINS", 60)


# the name of this website
NEWS_SITE_NAME = getattr(settings, "NEWS_SITE_NAME", "Swoosh News")


# emails for errors in ipn payment
NEWS_PAY_ERR_MAIL_FROM = getattr(settings, "NEWS_PAY_ERR_MAIL_FROM", 'root@localhost')
NEWS_PAY_ERR_MAIL_TO = getattr(settings, "NEWS_PAY_ERR_MAIL_TO", 'root@localhost')


# number of comments points users get per dollar.  As it stands,
# users will get 100 comment points when paying one dollar.
NEWS_COMMENT_PTS_PER_DOL = getattr(settings, "NEWS_COMMENT_PTS_PER_DOL", 100)

# A dictionary with the number of prices and description strings
# for the number of comments points users can buy.
NEWS_COMMENT_PRICES = getattr(settings, "NEWS_COMMENT_PRICES", \
        [(50, "50 $0.50"), 
         (100, "100 $1.00"), 
         (300, "300 $3.00"), 
         (500, "500 $5.00"), 
         (1000, "1000 $10.00")])

# number of comment points it costs to respond to regular news item
NEWS_COST_RESPOND_NEWS_ITEM = getattr(settings, \
        "NEWS_COST_RESPOND_NEWS_ITEM", 2)
# number of comment points it costs to respond to an "Ask SN" news item
NEWS_COST_RESPOND_ASK_SN = getattr(settings, \
        "NEWS_COST_RESPOND_ASK_SN", 0)

# number of comment points it costs to vote on a comment to a normal news item 
# up or down
NEWS_COST_VOTE_NORMAL_COMMENT = getattr(settings, \
        "NEWS_COST_VOTE_NORMAL_COMMENT", 1)
# number of comment points it costs to vote on a comment to an "ASK SN" news item 
# up or down
NEWS_COST_VOTE_ASK_SN_COMMENT = getattr(settings, \
        "NEWS_COST_VOTE_ASK_SN_COMMENT", 0)

# number of comment points it costs to vote a regular news item up or down
NEWS_COST_VOTE_NEWS_ITEM = getattr(settings, \
        "NEWS_COST_VOTE_NEWS_ITEM", 0)
# number of comment points it costs to vote an "Ask SN" news item up or down
NEWS_COST_VOTE_ASK_SN = getattr(settings, \
        "NEWS_COST_VOTE_ASK_SN", 0)


# lock file used with the update_ranking program in 
# news_app/scripts/update_ranking.py.  This is used
# so that two update_ranking programs will not run
# at the same time and step on each other's toes.
NEWS_UPDATE_RANKING_LOCKFILE = getattr(settings, "NEWS_UPDATE_RANKING_LOCKFILE", \
        "/var/lock/swoosh_news.update_ranking.lock")

# tells how many items should be shown on the frontpage
NEWS_ITEMS_FRONTPAGE = getattr(settings, "NEWS_ITEMS_FRONTPAGE", 15)


# Should we use the Paypal sandbox when accepting payments or the real site?
NEWS_PAYPAL_USE_SANDBOX = getattr(settings, "NEWS_PAYPAL_USE_SANDBOX", True)

# The button id for our paypal button.
NEWS_PAYPAL_HOSTED_BUTTON_ID = getattr(settings, "NEWS_PAYPAL_HOSTED_BUTTON_ID", 1055099)
