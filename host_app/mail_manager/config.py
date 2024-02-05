from host_app.mail_manager.mail_constants import MailConstants, get_mail_html
from host_app.mail_manager import mail_util

'''
1. account creation otp
2. password chaged otp
3. order creation otp 
4. order status
'''


to_address = 'tukurtukur777@gmail.com'
get_subject = {
    1:"Account Created Successfully", 2:"Password Has been Updated Successfully", 3:"Order Created Successfully" , 4:"Order Updated Successfully", 5:"Service Account Verified Successfully"
}

# user - email, username, password
def get_account_body(type, user : dict):
    subject = get_subject[type]
    body = f"""Your account has been created. Kindly use this <b> Password : {user["password"]} </b> to login and activate it for further usage. You can change the password anytime  </p>"""
    user["body"] = body
    user["subject"] = subject
    msg = get_mail_html(user)
    return msg

# user - email, username
def get_password_body(user : dict):
    body = f"""<p>Hello {user["username"]}, <br> Your password has been updaed. </p>"""
    return body

# user - email, username, order_id
def get_order_body(user : dict):
    body = f"""<p>Hello {user["username"]}, <br> Your order (OrderId : {user["order_id"]}) has been received. </p>"""
    return body

# user - email, username, order_id, order_status in string
def get_order_status_body(type:int, user : dict):
    subject = get_subject[type]
    body = f"""Your order (OrderId : {user["order_id"]}) has been updated. <br>  <b> Current Status : {user["status"]} </b> </p>"""
    user["body"] = body
    user["subject"] = subject
    msg =  get_mail_html(user)
    return msg


def send_email_to_client(type: int, user: dict):
    subj = get_subject[type]
    if type == 1 :
        message_body = get_account_body(1, user)
    elif type == 2 :
        message_body = get_password_body(user)
    elif type == 3 :
        message_body = get_order_body(user)
    elif type == 4 :
        message_body = get_order_status_body(user)

    to_address = user["email"]
    
    mail_util.send_email(to_address, subj, message_body)
    print(" MAIL SEND ")




'''
1. account creation mail with temp password
2. password has been changed mail
3. order created
4. order update
5. service creation mail
6. service 

'''