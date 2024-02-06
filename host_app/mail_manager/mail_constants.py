class MailConstants:
    # type name
    SUBJCET="subject"
    BODY="body"
    ACCOUNT_CREATION="account_creation"
    PASSWORD_UPDATED="password_verified"
    ORDER_CREATION="order_creation"
    ORDER_UPDATE="order_update"
    SERVICE_ACCOUNT_CREATION="service_account_creation"



def get_mail_html(user:dict):
    msg_body = f"""<!DOCTYPE html>
<html>

<head>
    <title>Ebase Notification</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Lato&display=swap" rel="stylesheet">
</head>

<body style="font-family: 'Lato', sans-serif; margin: 0px; padding: 0px; overflow-x: hidden;">
    <table style="border-radius: 8px; max-width: 750px; width: 100%; height: 100px; margin: 10px auto;" cellpadding="0"
        cellspacing="0">
        <tr>
            <td style="vertical-align: middle; text-align: center;">
                <img src="https://firebasestorage.googleapis.com/v0/b/ets-space-6d72d.appspot.com/o/Test%2Ficon-removebg-preview.png?alt=media&token=d4c1ec05-c06b-40e0-b53b-2721a9f33d33"
                    style="width: 100px; height: 100px;" alt="logo" />
            </td>
        </tr>
    </table>
    <table
        style="background-color: white; border-radius: 8px; max-width: 750px; width: 100%; margin: 0px auto; height: 100px; padding: 15px 15px 30px 15px;"
        cellpadding="0" cellspacing="0">
        <tr>
            <td style="color: #343434; font-size: 24px; text-align: center; font-weight: bold; padding: 10px 0px;">
                {user["subject"]}
            </td>
        </tr>
        <tr>
            <td>
                <b style="display: block; color: #343434; font-size: 20px; padding-bottom: 10px;">Hello {user["username"]}</b>
                <span style="display: block; font-size: 17px;color: #343434;">{user["body"]}
                    <br>
                    <br>
                    Regards,
                    <br>
                    Ebase
                    
                </span>
            </td>
        </tr>
    </table>
    <table style="max-width: 750px; width: 100%; height: 80px; border-radius: 8px; margin: 15px auto;">
        <tr>
            <td style="text-align: center; font-size: 18px;">
                <b>2024 @ Ebase all rights reserved. </b>
                <a href="mailto:ebasebusiness123@gmail.com" style="text-decoration: none;">
                    <b style="margin-left: 10px;">ebasebusiness123@gmail.com</b>
                </a>
            </td>
        </tr>
    </table>
</body>

</html>"""
    return msg_body