TITLE="EBase"
VERSION="0.2.1"
SUMMARY="E-Commerce Backend as A Service"
DESCRIPTION=f'''
{TITLE} API helps you do awesome stuff. 🚀
[API documentation](https://whosarghya.notion.site/Crux-892189b15a894bf28e946d6c983e2d8b)

## Items

You can **read items**.

## Users

You will be able to:

* **Create users** (_not implemented_).
* **Read users** (_not implemented_).
'''

TAGS_METADATA=[
    {
        "name": "user",
        "description": "Operations with users. The **login** logic is also here.",
    },
    {
        "name": "public",
        "description": "Manage items. So _fancy_ they have their own docs.",
        "externalDocs": {
            "description": "Items external docs",
            "url": "https://fastapi.tiangolo.com/",
        },
    },
]