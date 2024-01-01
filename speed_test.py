
import requests
import json

def trigger_request_with_api_key_and_body():
    url = 'https://test2-kyfh.onrender.com/public/signup'
    api_key = 'CRUX_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcGlfa2V5IjoialZRQW9RQXJhYTF1MnJKTmQzcXlXcGJYamk0ZC03OTdVenVndFlCSFRTQSJ9.KsM260E6yfj6IqZvQWzszjpfDfLx4MwuznJmTAP5KWI'

    headers = {
        'api_key': api_key,
        'Content-Type': 'application/json',  # Assuming JSON data in the request body
        # Add any other headers if required
    }

    phone = 1111112
    try:
        for i in range(1,100):
            email = "test" + str(i) + "@testmail.com"
            phone = phone + i 
            phoneStr = str(phone) 
            
            data = {
                "email" : email,
                "password" : "test123",
                "phone" : phoneStr,
                "service_org" : "BT"
            }
            
            response = requests.post(url, headers=headers, data=json.dumps(data))
            
            if response.status_code == 200:
                print("Request successful!")
                print("Response content:", response.text)
            else:
                print(f"Request failed with status code: {response.status_code}")
                print("Response content:", response.text)

    except requests.RequestException as e:
        print("Request failed:", e)

# Call the function to trigger the request
trigger_request_with_api_key_and_body()
