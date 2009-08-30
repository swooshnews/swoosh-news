from django.conf.urls.defaults import *

urlpatterns = patterns('news.views',

    (r'^$', 'news_items.index'),
    (r'^new/?$', 'news_items.new_news_items'),
    (r'^news_item/(?P<news_item_id>\d+)/?$', 'news_items.news_item'),
    (r'^submit/?$', 'news_items.submit'),

    (r'^new_comments/?$', 'comments.new_comments'),
    (r'^comment/(?P<comment_id>\d+)/?$', 'comments.comment'),
    (r'^submit_comment/?$', 'comments.submit_comment'),
    (r'^edit_comment/(?P<comment_id>\d+)/?$', 'comments.edit_comment'),

    (r'^delete/(?P<rankable_id>\d+)/?$', 'rankables.delete_rankable'),

    (r'^user/(?P<username>\w+)/?$', 'users.user'),

    (r'^login/?$', 'login.login_view'),
    (r'^logout/?$', 'login.logout_view'),
    (r'^create_account/?$', 'login.create_account'),
    (r'^change_password/?$', 'login.change_password'),

    (r'^vote/?$', 'voting.vote'),

    (r'^buy_points/?$', 'payment.buy_points'),
    (r'^receive_ipn/?$', include('paypal.standard.ipn.urls')),
    (r'^cancel/?$', 'payment.cancel'),
    (r'^success/?$', 'payment.success'),

    (r'^about/?$', 'text.about'),
    (r'^guidelines/?$', 'text.guidelines'),
    (r'^faq/?$', 'text.faq'),
    (r'^bookmarklet/?$', 'text.bookmarklet'),
    (r'^price/?$', 'text.price'),
)
