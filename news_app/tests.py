"""
This holds the unit tests for this app.
"""
from django.core.urlresolvers import reverse
from django.contrib.sessions.backends.db import SessionStore
from django.http import QueryDict, Http404
from django.test import TestCase

from urlparse import urlsplit

from news.models import UserProfile, NewsItem, Comment
from django.contrib.auth.models import User 
from news.validation import valid_comment_text, valid_email, \
        valid_next_redirect, valid_password, valid_text, valid_title, \
        valid_url, valid_username
from news.conf import *
from news.helpers import get_frontpage_querymanager, get_child_comments, \
        get_next_with_pages, datetime_ago, improve_url, assert_or_404
from news.views.news_items import check_submission



class NewsBaseTestCase(TestCase):
    """
    Base class that has some helper functions.
    The rest of the tests extend this class.
    """


    """ 
    These fixtures can be produced by resetting the database back to 
    its initial state, running `news/scripts/init_db_vals.py`, and 
    `manage.py dumpdata > news/fixtures/test_fixtures.json`.
    This will create the needed and expected test fixtures.
    """
    fixtures = ['test_fixtures.json']

    def setUp(self):
        """
        Make sure no one is logged in.
        """
        self.assertNotLoggedIn(self.client)

    def followRedirect(self, response, expected_url=None):
        """
        Do a GET on the URL from a redirected response
        and return that response.
        """
        # This can't be called because it loads the
        # expected url, which will mess up session stuff
        # self.assertRedirects(response, expected_url)

        self.assert_('Location' in response)
        redirect_url = response['Location']

        scheme, netloc, path, query, fragment = urlsplit(redirect_url)
        # Get the redirection page, using the same client that was used
        # to obtain the original response.
        redirect_response = response.client.get(path, QueryDict(query))

        return redirect_response

    def login_user(self, client, username, password, next):
        """
        Logs the user in and returns the response.
        Makes sure the response is being redirected to the 
        correct place.
        """
        # try to login
        response = client.post(reverse('news.views.login.login_view'), 
                               {'username': username, 'password': password, 
                                'next': next})

        # make sure user is now logged in
        self.assertUserLoggedIn(client, username)

        # make sure it's a redirection
        self.assertRedirects(response, next)

        return response

    def logout_user(self, client, next=''):
        """
        Log out the user.
        """
        #if not next:
        #   next = '/'

        client.get(reverse('news.views.login.logout_view')) 

        self.assertNotLoggedIn(client)

    def assert404(self, response):
        """
        Makes sure the response is a 404.
        """
        self.failUnlessEqual(response.status_code, 404)

    def assertInSession(self, response, **kwargs):
        """ 
        Take the kwargs, translate them to session variables,
        and make sure they exist in the session.
        """
        # get session
        self.assert_('sessionid' in response.cookies)
        sesh = SessionStore(session_key=response.cookies.get('sessionid').value)
        
        for key in kwargs:
            self.assert_(key in sesh)
            self.assertEquals(sesh[key], kwargs[key])

    def assertNotLoggedIn(self, client):
        """
        Asserts the that current user is not logged in.
        """
        if 'sessionid' in client.cookies:
            sesh = SessionStore(session_key=client.cookies.get('sessionid').value)
            self.assert_('_auth_user_id' not in sesh)

    def assertUserLoggedIn(self, client, username):
        """
        Assert that user is logged in.
        """
        self.assert_('sessionid' in client.cookies)
        sesh = SessionStore(session_key=client.cookies.get('sessionid').value)
        self.assert_('_auth_user_id' in sesh)
        sesh_user = User.objects.get(id=sesh['_auth_user_id'])
        self.assertEqual(sesh_user.username, username)

    def assertFalse(self, expr):
        """ This is the opposite of assert_. """
        self.assert_(expr == False)


class NewsCommentTests(NewsBaseTestCase):
    """ These are tests for submitting comments. """
    def do_submit_comment(self, client, parent_id='', comment_text='', 
            username='ice', password='iceiceice'):
        """
        This does all the work with actually submitting comments and making
        sure the correct thing happens whether we are posting to another 
        comment or a news item.
        """

        submit_com_view = reverse('news.views.comments.submit_comment') 

        # if comment text is blank a lot of session variables are set
        # and we are redirected back to the news item or comment we came from.
        # Test both posting to a comment and posting to a news item.
        response = client.post(submit_com_view, 
                {'parent_id': parent_id, 'comment_text': ''})

        if Comment.objects.filter(id=parent_id):
            next = reverse('news.views.comments.comment', 
                    args=(parent_id,))
        else:
            next = reverse('news.views.news_items.news_item',
                    args=(parent_id,))


        self.assertInSession(response, comment_posting_error="Comment not valid",
                comment_text_for_id=parent_id)
        self.assertRedirects(response, next)

        # make sure no one is logged in before we try the next step
        self.assertNotLoggedIn(client)

        # try posting without being logged in
        response = client.post(submit_com_view, 
            {'parent_id': parent_id, 'comment_text': comment_text})


        # the user is not logged in, so when we try to post a valid comment,
        # we get redirected to login_view()
        self.assertInSession(response, comment_text=comment_text,
                comment_text_for_id=parent_id)
        self.assertRedirects(response, 
                reverse('news.views.login.login_view') + "?next=" + next)

        # actually login user
        self.login_user(client, username, password, next)

        # get the number of comments so far
        # (we will use this later to make sure one more comment
        # was posted)
        num_coms = Comment.objects.count()

        # now post comment
        response = client.post(submit_com_view, 
            {'parent_id': parent_id, 'comment_text': comment_text})

        # make sure the comment has been posted
        self.assertEquals(num_coms + 1, Comment.objects.count())

        # make sure we are redirected either back to the 
        # comment page or the news item page and 
        # follow the redirection
        redirect_response = self.followRedirect(response, next)

        # make sure the page contains our new comment
        self.assert_(comment_text in redirect_response.content)

    def testSubmitComment(self):
        """
        Test comment submission functionality.
        """
        submit_com_view = reverse('news.views.comments.submit_comment') 

        # 404 on get
        self.assert404(self.client.get(submit_com_view))

        # 404 if 'parent_id' or 'comment_text' is not present
        self.assert404(self.client.post(submit_com_view, {'parent_id':4}))
        self.assert404(self.client.post(submit_com_view, {'comment_text':'al'}))

        # try responding to a comment
        self.do_submit_comment(self.client, parent_id=4, 
                comment_text="abcdefghijklmnop")

        # must log out
        self.logout_user(self.client)

        # try responding to a news item
        self.do_submit_comment(self.client, parent_id=1, 
                comment_text="abcdefghijklmnop")


class NewsLoginTests(NewsBaseTestCase):
    """ Tests for dealing with logging in, creating users, etc.  """
    def testLogout(self):
        """
        This tests the logout_view.
        """
        # try to logout without being logged in
        self.assertNotLoggedIn(self.client)
        response = self.client.get(reverse('news.views.login.logout_view')) 
        self.assertEquals(response.status_code, 302)
        self.assertNotLoggedIn(self.client)

        # now make sure logout will actually log us out
        self.login_user(self.client, 'ice', 'iceiceice', 
                reverse('news.views.news_items.index'))
        response = self.client.get(reverse('news.views.login.logout_view')) 
        self.assertEquals(response.status_code, 302)
        self.assertNotLoggedIn(self.client)

    def testLogin(self):
        """
        This tests the login_view.
        """
        # TODO: this
        next = reverse('news.views.users.user', args=('ice',))
        login_view = reverse('news.views.login.login_view')

        # make sure 200 on GET
        self.assertEquals(self.client.get(login_view).status_code, 200)

        # 404 if invalid redirect
        response = self.client.post(login_view + '?next=apple', 
                {'username':"lalala", 'password': "lalala", })
        self.assert404(response)

        # 404 in no username or password
        self.assert404(self.client.post(login_view, {'password': "lalala", }))
        self.assert404(self.client.post(login_view, {'username': "lalala", }))

        # make sure no one is logged in
        self.assertNotLoggedIn(self.client)

        going_to = reverse('news.views.news_items.new_news_items')

        # error if incorrect username or password
        response = self.client.post(login_view, 
                {'username':"ice", 'password': "plants", 'next': going_to})
        self.assertInSession(response, 
                login_error="Invalid username or password", 
                login_username='ice') 
        redirect_response = self.followRedirect(response, 
                login_view + '?next=' + going_to)
        self.assertContains(redirect_response, 'Invalid username or password')

        # try logging them in and make sure they are logged in
        response = self.client.post(login_view, 
                {'username':"ice", 'password': "iceiceice", 'next': going_to})
        self.assertRedirects(response, going_to)
        self.assertUserLoggedIn(self.client, 'ice')

    def testCreateAccount(self):
        """
        Test the create_account view.
        """
        create_account_view = reverse('news.views.login.create_account')

        # it should fail if we don't pass it a valid next redirect
        response = self.client.post(create_account_view + '?next=apple', 
                {'username':"lalala", 'password': "lalala", })
        self.assert404(response)

        # it should fail if it's not a POST
        self.assert404(self.client.get(create_account_view))

        # it shoudl fail if we either don't have username or password
        self.assert404(self.client.post(create_account_view, 
            {'password': "lalala", }))
        self.assert404(self.client.post(create_account_view, 
            {'username': "lalala", }))

        # if our username is not valid (we should be redirected back 
        # to the login page, but our failed username should still be
        # in the box
        response = self.client.post(create_account_view, 
                {'username':"asefasef.", 'password': "lalala",
                 'next': reverse('news.views.news_items.index')})
        self.assertInSession(response, create_account_error='Username can only ' + 
            'consist of letters, numbers, and underscores, and must be ' + 
            'less than 30 characters', create_account_username='asefasef.') 
        redirect_response = self.followRedirect(response, 
            reverse('news.views.login.login_view') + '?next=' +
            reverse('news.views.news_items.index'))
        self.assertContains(redirect_response, 'asefasef.')

        # make sure it errors if any other users have this username
        response = self.client.post(create_account_view, 
                {'username':"ice", 'password': "lalala", })
        self.assertInSession(response, 
                create_account_error='Username ice taken', 
                create_account_username='ice') 
        redirect_response = self.followRedirect(response, 
                reverse('news.views.login.login_view') + '?next=' +
                reverse('news.views.news_items.index'))
        self.assertContains(redirect_response, 'ice')

        # make sure it errors if the password is not valid
        response = self.client.post(create_account_view, 
                {'username':"peanut", 'password': "", })
        self.assertInSession(response, 
                create_account_error='Password cannot be blank and ' +
                    'must be less than 30 characters',
                create_account_username='peanut') 
        redirect_response = self.followRedirect(response, 
                reverse('news.views.login.login_view') + '?next=' +
                reverse('news.views.news_items.index'))
        self.assertContains(redirect_response, 'peanut')

        # now do it for real and make sure the new user has been created
        response = self.client.post(create_account_view, 
                {'username':"giraffe", 'password': "two", })
        self.assertUserLoggedIn(self.client, "giraffe")
        self.assert_(len(User.objects.filter(username="giraffe")) > 0)
        self.assert_(len(UserProfile.objects.filter(user__username="giraffe")) > 0)

    def testChangePassword(self):
        """ 
        Test the change password view.
        """
        change_pass_view = reverse('news.views.login.change_password')

        # if the user is not logged in, redirect to login page
        response = self.client.get(change_pass_view) 
        self.assertRedirects(response, 
                reverse('news.views.login.login_view') + '?next=' +
                change_pass_view)

        # login and use a logged in user from here on out
        self.login_user(self.client, "ice", "iceiceice", change_pass_view)

        # 404 if don't include 'password1' or 'password2' in POST
        self.assert404(self.client.post(change_pass_view, {'password1':'hello'}))
        self.assert404(self.client.post(change_pass_view, {'password2':'hello'}))

        # we get error message if the passwords don't match
        response = self.client.post(change_pass_view, 
                {'password1':"peanut", 'password2': "fish", })
        self.assertInSession(response, 
                change_password_error='Passwords do not match')
        redirect_response = self.followRedirect(response, change_pass_view)
        self.assertContains(redirect_response, 'Passwords do not match')

        # we get an error message if the passwords match but are not valid
        response = self.client.post(change_pass_view, 
                {'password1':"", 'password2': "", })
        self.assertInSession(response, 
                change_password_error='Password too long or blank')
        redirect_response = self.followRedirect(response, change_pass_view)
        self.assertContains(redirect_response, 'Password too long or blank')

        # now actually change the password
        response = self.client.post(change_pass_view, 
                {'password1':"new_pass", 'password2': "new_pass", })
        self.assertRedirects(response, 
                reverse('news.views.users.user', args=('ice',)))

        # log out and make sure we can login with new information
        self.logout_user(self.client)
        self.login_user(self.client, "ice", "new_pass", change_pass_view)
        self.assertUserLoggedIn(self.client, "ice")


class NewsValidationTests(NewsBaseTestCase):
    """ Test the validation of different fields. """
        
    def testValidCommentText(self):
        """ Test valid_comment_text(). """

        # blank comments should not be valid
        self.assertFalse(valid_comment_text(''))

        # anything else should be valid
        self.assert_(valid_comment_text('asefasef'))
        self.assert_(valid_comment_text('.'))
        self.assert_(valid_comment_text('\n'))
        self.assert_(valid_comment_text('what. this is a long paragraph.'))
        

    def testValidEmail(self):
        """ Test valid_email(). """

        # everything should be valid 
        self.assert_(valid_email('asefasef'))
        self.assert_(valid_email('lala@email.com'))
        self.assert_(valid_email('.'))
        self.assert_(valid_email(''))
        self.assert_(valid_email('a' * (NEWS_MAX_EMAIL_LENGTH)))
        # except it can't be too long
        self.assertFalse(valid_email('a' * (NEWS_MAX_EMAIL_LENGTH + 1)))

    def testValidNextRedirect(self):
        """ Test valid_next_redirect(). """

        # if the redirect can't be resolved to a view, then there is probably nothing
        # wrong
        self.assertFalse(valid_next_redirect("http://google.com"))
        self.assertFalse(valid_next_redirect("http://google.com/"))
        self.assertFalse(valid_next_redirect("http://google.com/new"))
        self.assertFalse(
                valid_next_redirect(reverse('news.views.login.login_view')+'a'))

        # everything that can be resolved to a view is probably okay
        self.assert_(valid_next_redirect(reverse('news.views.login.login_view')))
        self.assert_(valid_next_redirect(
            reverse('news.views.users.user', args=('ice',))))
        self.assert_(valid_next_redirect(
            reverse('news.views.login.login_view') + '?what=who'))
        self.assert_(valid_next_redirect(
            reverse('news.views.login.login_view') + '#other?what=who'))

    def testValidPassword(self):
        """ Test valid_password(). """

        # everything is okay
        self.assert_(valid_password('@#$!@#$%^'))
        self.assert_(valid_password('....'))
        self.assert_(valid_password('a;3irjq;3 jra;ijaij a;a'))
        self.assert_(valid_password('thisis a pass'))
        self.assert_(valid_password('a' * NEWS_MAX_PASSWORD_LENGTH))

        # unless it is too long or blank
        self.assertFalse(valid_password('a' * (NEWS_MAX_PASSWORD_LENGTH + 1)))
        self.assertFalse(valid_password(''))

    def testValidText(self):
        """ Test valid_text(). """

        # everything is okay
        # valid_text always returns true
        pass

    def testValidTitle(self):
        """ Test valid_title(). """

        # everything is okay
        self.assert_(valid_title('@#$!@#$%^'))
        self.assert_(valid_title('....'))
        self.assert_(valid_title('a;3irjq;3 jra;ijaij a;a'))
        self.assert_(valid_title('thisis a pass'))
        self.assert_(valid_title('a' * NEWS_MAX_TITLE_LENGTH))

        # unless it is too long or blank
        self.assertFalse(valid_title('a' * (NEWS_MAX_TITLE_LENGTH + 1)))
        self.assertFalse(valid_title(''))

    def testValidURL(self):
        """ Test valid_url(). """

        # normal urls are okay
        baseURL = 'http://google.com/'
        self.assert_(valid_url(baseURL))
        self.assert_(valid_url('https://google.com'))
        self.assert_(valid_url(baseURL + \
                'o' * (NEWS_MAX_URL_LENGTH - len(baseURL))))

        # but it needs http or https
        self.assertFalse(valid_url('google.com'))
        self.assertFalse(valid_url('ftp://google.com'))

        # it also needs to to have a '.' in the domain name
        self.assertFalse(valid_url('http://google/'))

        # it also must not be too long
        self.assertFalse(valid_url(baseURL + \
                'o' * (NEWS_MAX_URL_LENGTH - len(baseURL) + 1)))

    def testValidUsername(self):
        """ Test valid_username(). """

        # usernames must match \w+
        self.assert_(valid_username('user'))
        self.assert_(valid_username('32__328LALAuser'))
        self.assert_(valid_username('_'))
        self.assert_(valid_username('a' * NEWS_MAX_USERNAME_LENGTH))

        self.assertFalse(valid_username('!#^#$'))
        self.assertFalse(valid_username(''))
        self.assertFalse(valid_username('\n'))
        self.assertFalse(valid_username('66.66'))
        self.assertFalse(valid_username('doctor user'))
        self.assertFalse(valid_username('日本語'))

        # usernames must not be too long
        self.assertFalse(valid_username('a' * (NEWS_MAX_USERNAME_LENGTH + 1)))


class NewsHelperTests(NewsBaseTestCase):
    """ Test the helpers. """

    def testGetFrontpageQuerymanager(self):
        """ Test get_frontpage_querymanager(). """
        front_querymanager = get_frontpage_querymanager()

        expected_querymanager = \
                NewsItem.objects.filter(date_posted__gt=(datetime_ago(weeks=4)))
        expected_querymanager = expected_querymanager.order_by('-ranking')

        for item in front_querymanager:
            self.assert_(item in expected_querymanager)

    def testGetChildComments(self):
        """ Test get_child_comments(). """
        newsitem = NewsItem.objects.get(id=1)
        child_comments = get_child_comments(newsitem.child_set)
        for com_data in child_comments:
            self.assert_(com_data['comment'] in Comment.objects.all())


    def testGetNextWithPages(self):
        """ Test get_next_with_pages(). """
        self.assertEquals(get_next_with_pages('/', 1), '/')
        self.assertEquals(get_next_with_pages('/', 2), '%2F%3Fpage%3D2')

    def testDatetimeAgo(self):
        """ Test datetime_ago(). """
        # TODO: write this

    def testImproveURL(self):
        """ Test improve_url(). """
        self.assertEquals(improve_url('http://google.com'), 'http://google.com')
        self.assertEquals(improve_url('google.com'), 'http://google.com')

    def testMyAssert(self):
        """ Test assert_or_404(). """
        self.assertRaises(Http404, assert_or_404, False)
        assert_or_404(True)


class NewsNewsItemTests(NewsBaseTestCase):
    """ Test the news item views. """

    def testCheckSubmission(self):
        """ Test submission checker for news stories. """

        # Make sure that the basic submission is okay.
        # It returns "" on sucess.
        self.assertEquals(check_submission('title', 'http://google.com', ''), '')
        self.assertEquals(check_submission('title', '', 'some text'), '')
        self.assertEquals(check_submission('a' * NEWS_MAX_TITLE_LENGTH, 
                                           '', 'some text'), '')

        # now make sure it returns an error if the title to too long or too short
        self.assert_(check_submission('a' * (NEWS_MAX_TITLE_LENGTH + 1),
                                      '', 'some text') != '')

        # return an error if url and text are not set
        self.assertEquals(check_submission('title', '', ''), 
                          "Enter url or text")

        # return error if both are set
        self.assertEquals(
                check_submission('title', 'http://google.com', 'what'),
                'Only url OR text (not both)')

        # make sure it catches invalid urls
        self.assertEquals(
                check_submission('title', 'http:/google.com', ''),
                'URL not valid')



