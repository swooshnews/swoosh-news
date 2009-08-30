

from django import template
from django.template.defaultfilters import timesince as django_timesince
from django.template.defaulttags import IfEqualNode
from django.template import TemplateSyntaxError, Node, NodeList

from urlparse import urlparse

register = template.Library()

@register.filter
def abbr_timesince(value, arg=None):
    """
    Returns an abbreviated timesince, which only displays the first 
    value.  So, {{ date|abbr_timesince }} becomes just "10 days",
    instead of "10 days, 15 hours".
    """
    return django_timesince(value, arg).split(',')[0]
abbr_timesince.is_safe = False

@register.filter
def multiply(value, arg=1):
    """
    Returns the value multiplied by the argument
    """
    return int(value) * int(arg)
multiply.is_safe = False

@register.filter
def float_multiply(value, arg=1):
    """
    Returns the value multiplied by the argument
    """
    return float(value) * float(arg)
float_multiply.is_safe = False

@register.filter
def float_divide(value, arg=1):
    """
    Returns the value multiplied by the argument
    """
    # don't give divide by 0 error
    if arg == 0:
        return 0
    return float(value) / float(arg)
float_divide.is_safe = False

@register.filter
def subtract(value, arg=0):
    """
    Returns the value multiplied by the argument
    """
    return int(value) - int(arg)
subtract.is_safe = False

class IfUrlPathEqualNode(Node):
    def __init__(self, var1, var2, nodelist_true, nodelist_false, negate):
        self.var1, self.var2 = var1, var2
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false
        self.negate = negate

    def __repr__(self):
        return "<IfUrlPathEqualNode>"

    def render(self, context):
        val1 = self.var1.resolve(context, True)
        val2 = self.var2.resolve(context, True)
        (_, _, path1, _, _, _) = urlparse(val1)
        (_, _, path2, _, _, _) = urlparse(val2)
        if (self.negate and path1 != path2) or (not self.negate and path1 == path2):
            return self.nodelist_true.render(context)
        return self.nodelist_false.render(context)


def do_ifurlpathequal(parser, token, negate):
    bits = list(token.split_contents())
    if len(bits) != 3:
        raise TemplateSyntaxError, "%r takes two arguments" % bits[0]
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    val1 = parser.compile_filter(bits[1])
    val2 = parser.compile_filter(bits[2])


    return IfUrlPathEqualNode(val1, val2, nodelist_true, nodelist_false, negate)

@register.tag
def ifurlpathequal(parser, token):
    """
    Outputs the contents of the block if the two url's paths equal each other.

    Examples::

        {% ifurlpathequal "/new" request.path %}
            ...
        {% endifurlpathequal %}

        {% ifnoturlpathequal user.id comment.user_id %}
            ...
        {% else %}
            ...
        {% endifnoturlpathequal %}
    """
    return do_ifurlpathequal(parser, token, False)


@register.tag
def ifnoturlpathequal(parser, token):
    """
    Outputs the contents of the block if the two arguments are not equal.
    See ifurlpathequal.
    """
    return do_ifurlpathequal(parser, token, True)


class IfLessThan(Node):
    def __init__(self, var1, var2, nodelist_true, nodelist_false, negate):
        self.var1, self.var2 = var1, var2
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false
        self.negate = negate

    def __repr__(self):
        return "<IfLessThan>"

    def render(self, context):
        val1 = self.var1.resolve(context, True)
        val2 = self.var2.resolve(context, True)
        if (self.negate and val1 >= val2) or (not self.negate and val1 < val2):
            return self.nodelist_true.render(context)
        return self.nodelist_false.render(context)


def do_iflessthan(parser, token, negate):
    bits = list(token.split_contents())
    if len(bits) != 3:
        raise TemplateSyntaxError, "%r takes two arguments" % bits[0]
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    val1 = parser.compile_filter(bits[1])
    val2 = parser.compile_filter(bits[2])

    return IfLessThan(val1, val2, nodelist_true, nodelist_false, negate)

@ register.tag
def iflessthan(parser, token):
    """
    Outputs the contents of the block if the first arg is less than the second.

    Examples::

        {% iflessthan arg 10 %}
            ...
        {% endiflessthan %}

        {% ifnotlessthan user.id comment.user_id %}
            ...
        {% else %}
            ...
        {% endifnotlessthan %}
    """
    return do_iflessthan(parser, token, False)

@register.tag
def ifnotlessthan(parser, token):
    """
    Outputs the contents of the block if the first arg is less than the second.
    See iflessthan.
    """
    return do_iflessthan(parser, token, True)



class IfEditRankable(Node):
    def __init__(self, var1, var2, nodelist_true, nodelist_false, negate):
        self.var1, self.var2 = var1, var2
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false
        self.negate = negate

    def __repr__(self):
        return "<IfEditRankableNode>"

    def render(self, context):
        rankable = self.var1.resolve(context, True)
        userprofile = self.var2.resolve(context, True)
        if (self.negate and not rankable.can_be_edited(userprofile)) or \
                (not self.negate and rankable.can_be_edited(userprofile)):
            return self.nodelist_true.render(context)
        return self.nodelist_false.render(context)


def do_ifeditrankable(parser, token, negate):
    bits = list(token.split_contents())
    if len(bits) != 3:
        raise TemplateSyntaxError, "%r takes two arguments" % bits[0]
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    val1 = parser.compile_filter(bits[1])
    val2 = parser.compile_filter(bits[2])


    return IfEditRankable(val1, val2, nodelist_true, nodelist_false, negate)

@register.tag
def ifeditrankable(parser, token):
    """
    Outputs the contents of the block if the two url's paths equal each other.

    Examples::

        {% ifeditrankable comment user.get_profile %}
            ...
        {% endifeditrankable %}

        {% ifnoteditrankable news_item user.get_profile %}
            ...
        {% else %}
            ...
        {% endifnoteditrankable %}
    """
    return do_ifeditrankable(parser, token, False)


@register.tag
def ifnoteditrankable(parser, token):
    """
    Outputs the contents of the block if the two arguments are not equal.
    See ifeditrankable.
    """
    return do_ifeditrankable(parser, token, True)



class IfAlreadyVoted(Node):
    def __init__(self, var1, var2, nodelist_true, nodelist_false, negate):
        self.var1, self.var2 = var1, var2
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false
        self.negate = negate

    def __repr__(self):
        return "<IfAlreadyVoted>"

    def render(self, context):
        rankable = self.var1.resolve(context, True)
        userprofile = self.var2.resolve(context, True)
        if (self.negate and not rankable.already_voted(userprofile)) or \
                (not self.negate and rankable.already_voted(userprofile)):
            return self.nodelist_true.render(context)
        return self.nodelist_false.render(context)


def do_ifalreadyvoted(parser, token, negate):
    bits = list(token.split_contents())
    if len(bits) != 3:
        raise TemplateSyntaxError, "%r takes two arguments" % bits[0]
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    val1 = parser.compile_filter(bits[1])
    val2 = parser.compile_filter(bits[2])


    return IfAlreadyVoted(val1, val2, nodelist_true, nodelist_false, negate)

@register.tag
def ifalreadyvoted(parser, token):
    """
    Does true block is userprofile has already voted on rankable.

    Examples::

        {% ifalreadyvoted rankable user.get_profile %}
            ...
        {% endifalreadyvoted %}

        {% ifnotalreadyvoted news_item userprofile %}
            ...
        {% else %}
            ...
        {% endifnotalreadyvoted %}
    """
    return do_ifalreadyvoted(parser, token, False)


@register.tag
def ifnotalreadyvoted(parser, token):
    """
    See ifalreadyvoted.
    """
    return do_ifalreadyvoted(parser, token, True)






class IfCanPostComment(Node):
    def __init__(self, var1, var2, nodelist_true, nodelist_false, negate):
        self.var1, self.var2 = var1, var2
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false
        self.negate = negate

    def __repr__(self):
        return "<IfAlreadyVoted>"

    def render(self, context):
        userprofile = self.var1.resolve(context, True)
        rankable = self.var2.resolve(context, True)
        if (self.negate and not userprofile.comment_points >= \
                rankable.comment_cost(userprofile)) or \
                (not self.negate and userprofile.comment_points >= \
                rankable.comment_cost(userprofile)):
            return self.nodelist_true.render(context)
        return self.nodelist_false.render(context)


def do_ifcanpostcomment(parser, token, negate):
    bits = list(token.split_contents())
    if len(bits) != 3:
        raise TemplateSyntaxError, "%r takes two arguments" % bits[0]
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    val1 = parser.compile_filter(bits[1])
    val2 = parser.compile_filter(bits[2])


    return IfCanPostComment(val1, val2, nodelist_true, nodelist_false, negate)

@register.tag
def ifcanpostcomment(parser, token):
    """
    Does true block is userprofile has enough comment points to
    post a comment to the news item that is rankable's parent 
    (or to rankable if rankable is a news item).

    Examples::

        {% ifcanpostcomment user.get_profile rankable %}
            ...
        {% endifcanpostcomment %}

        {% ifnotcanpostcomment userprofile news_item %}
            ...
        {% else %}
            ...
        {% endifnotcanpostcomment %}
    """
    return do_ifcanpostcomment(parser, token, False)


@register.tag
def ifnotcanpostcomment(parser, token):
    """
    See ifcanpostcomment.
    """
    return do_ifcanpostcomment(parser, token, True)
