from host_app.mail_manager.mail_constants import MailConstants as mc
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


def get_account_body(user : dict):
    body = f"""<p>Hello {user["username"]}, <br> Your account has been created. Kindly use this <b> OTP : {user["otp"]} </b> to verify your account and activate it for further usage  </p>"""
    return body


def get_password_body(user : dict):
    body = f"""<p>Hello {user["username"]}, <br> Your password has been updaed. </p>"""


def send_email_to_client(type: int, user: dict):
    subj = get_subject[type]
    if type == 1 :
        message_body = get_account_body(user)
    elif type == 2 :
        message_body = get_password_body(user)

    to_address = user["email"]
    
    mail_util.send_email(to_address, subj, message_body)










'''
1. account creation mail with temp password
2. password has been changed mail
3. order created
4. order update
5. service creation mail
6. service 

'''