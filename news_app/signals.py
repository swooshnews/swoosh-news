from django.core.signals import request_finished
from django.core.mail import send_mail

from paypal.standard.ipn.signals import payment_was_successful, payment_was_flagged

import news.conf as news_settings


def process_successful_ipn_signal(sender, **kwargs):
    """
    Process an ipn sent by Paypal. Namely, add the comment points
    to a user's account, so they can make comments.
    """
    ipn_obj = sender

    # this needs to go here, because we import this file in news.models,
    # so UserProfile hasn't been defined yet
    from news.models import UserProfile

    # the custom field should be the same as the transaction_subject field
    if ipn_obj.custom != ipn_obj.transaction_subject:
        kwargs['err_on_success'] = "ipn_obj.custom (" + ipn_obj.custom + \
                ") does not equal ipn_obj.transaction_subject (" + \
                ipn_obj.transaction_subject + ")"
        return process_err_ipn_signal(sender, **kwargs)

    # the ipn object's transaction_subject field should hold the username
    if not UserProfile.objects.filter(user__username=ipn_obj.transaction_subject):
        kwargs['err_on_success'] = \
                "Username in ipn_obj.transaction_subject does not exist."
        return process_err_ipn_signal(sender, **kwargs)

    userprofile = UserProfile.objects.get(user__username=ipn_obj.transaction_subject)

    # Get the comment points and error-check them.
    # Make sure we don't add a fraction of a comment point to
    # someone's account.
    points = ipn_obj.mc_gross * 100
    if points <= 0 or points != int(points) or not points.is_finite(): 
        kwargs['err_on_success'] = \
                "comment points are less than 0, or there are some decimal points."
        return process_err_ipn_signal(sender, **kwargs)


    userprofile.comment_points += int(points)
    userprofile.save()

    import sys
    print >>sys.stderr, "Received payment, for " + str(ipn_obj.mc_gross) + \
            " from " + unicode(ipn_obj.custom)

payment_was_successful.connect(process_successful_ipn_signal)


def process_err_ipn_signal(sender, **kwargs):
    """
    Process an error in a Paypal payment.
    Send an email with error reporting stuff.
    """
    ipn_obj = sender

    import sys
    print >>sys.stderr, "Payment error, ipn id " + str(ipn_obj.id)


    # if err_on_success is in kwargs, that means the payment was otherwise 
    # successful, but there was an error in the things process_successful_ipn_signal
    # checks for.
    err_on_success = ''
    if 'err_on_success' in kwargs:
        err_on_success = kwargs['err_on_success']
    
    subject = news_settings.NEWS_SITE_NAME + " IPN error, id " + str(ipn_obj.id)

    # write the actual message
    message = "ID: " + str(ipn_obj.id) + "\n"
    if err_on_success:
        message += "Error from process_err_ipn_signal: " + err_on_success + "\n"
    if ipn_obj.flag:
        message += "Flag info: " + ipn_obj.flag_info + "\n"
    message += "\n"
    message += "Response: " + ipn_obj.response + "\n"
    message += "Transaction Subject: " + ipn_obj.transaction_subject + "\n"
    message += "Custom: " + ipn_obj.custom + "\n"
    message += "Quantity: " + str(ipn_obj.quantity) + "\n"
    message += "Option Name1: " + unicode(ipn_obj.option_name1) + "\n"  
    message += "Payer Status: " + unicode(ipn_obj.payer_status) + "\n" 
    message += "Payment Date: " + unicode(ipn_obj.payment_date) + "\n" 
    message += "Payment Gross: " + unicode(ipn_obj.payment_gross) + "\n" 
    message += "Payment Status: " + unicode(ipn_obj.payment_status) + "\n" 
    message += "Payment Type: " + unicode(ipn_obj.payment_type) + "\n" 
    message += "Name: " + unicode(ipn_obj.first_name) + " " + unicode(ipn_obj.last_name) + "\n" 
    message += "Payer Email: " + unicode(ipn_obj.payer_email) + "\n" 
    message += "Payer ID: " + unicode(ipn_obj.payer_id) + "\n" 
    message += "MC Currency: " + unicode(ipn_obj.mc_currency) + "\n" 
    message += "MC Fee: " + unicode(ipn_obj.mc_fee) + "\n" 
    message += "MC Gross: " + unicode(ipn_obj.mc_gross) + "\n" 
    message += "\n\n\n\n" 
    message += "query: " + unicode(ipn_obj.query) + "\n"

    send_mail(subject, message, news_settings.NEWS_PAY_ERR_MAIL_FROM, 
            [news_settings.NEWS_PAY_ERR_MAIL_TO])

payment_was_flagged.connect(process_err_ipn_signal)
