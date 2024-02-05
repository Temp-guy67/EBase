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
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            background-color: #f4f4f4;
            width: 100%;
        }}

        .navbar {{
            display: flex;
            width: 100%;
            height: 20vh;
            justify-content: center;
            background-color: black;

        }}

        .navbar img {{
            width: auto;
        }}

        .container {{
            margin: 0 auto;
            padding: 20px;
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }}

        .header {{
            margin-top: 2vh;
            text-align: center;
            color: #333333;
            font-size: 30px;
            font-weight: 500;
            margin-bottom: 20px;
        }}

        .content {{
            color: #555555;
            font-size: 20px;
            padding: 20px;
            margin: 10px 10px;
        }}
    </style>
</head>

<body>
    <div class="container">
        <div class="navbar" style="justify-content: center;">
            <img src="https://firebasestorage.googleapis.com/v0/b/ets-space-6d72d.appspot.com/o/Test%2Ficon.png?alt=media&token=798e796f-8703-454b-8c95-e26d98ffef3e"
                alt="main logo">
        </div>
        <div class="header">{user["subject"]}</div>
        <hr>
        <div class="content">
            Hi {user["username"]}, <br><br> {user["body"]}.
            <br><br><br>
            Regards,
            <br>
            Ebase
        </div>
        <div class="navbar" style="height: 5vh; align-items: center;">
            <p style="color: #ffffff;"> @2024 Ebase, All Rights Reserved </p>
        </div>
    </div>
</body>

</html>"""
    return msg_body