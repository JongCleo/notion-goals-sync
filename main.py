from dotenv import load_dotenv
from notion_client import Client
import os
import datetime
from dateutil.parser import parse
import uuid

load_dotenv()

origin_notion = Client(auth=os.environ["NOTION_SECRET_A"])
foreign_notion = Client(auth=os.environ["NOTION_SECRET_B"])

# Fetch +/- 1 week's worth of goals from origin
today = datetime.date.today()
margin = datetime.timedelta(days = 8)
response = origin_notion.databases.query(database_id=os.environ["TABLE_ID_A"])["results"]

origin_goals = [
    #goal["properties"]["Subgoal"]["title"][0]["plain_text"] 
    goal for goal in response
    if "Due" in goal["properties"]
    and goal["properties"]["Subgoal"]["title"][0]["plain_text"].strip() != ""
    and today - margin <= parse(goal["properties"]["Due"]["date"]["start"]).date() <= today + margin
]

for goal in origin_goals:
    if (goal["properties"]["uuid"]["rich_text"] == []):
        origin_notion.pages.update(
        **{
            "page_id": goal["id"],
            "properties": {
            "uuid": {
                "rich_text": [
                    {
                        "text": {
                            "content": str(uuid.uuid4())
                        }
                    }
                ]
            }            
            }        
        }
        )        
# - write uuids if DNE


# Fetch goals from foreign



# table with ID exists in foregin table but DNE in origin
# exists in origin but not in foreign