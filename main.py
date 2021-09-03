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

origin_primary_key = "Subgoal"
origin_due_date = "Due"
origin_goals = [    
    goal for goal in response
    if origin_due_date in goal["properties"]
    and goal["properties"][origin_primary_key]["title"][0]["plain_text"].strip() != ""
    and today - margin <= parse(goal["properties"][origin_due_date]["date"]["start"]).date() <= today + margin
]

# Create uuids if they do not already exist
for goal in origin_goals:
    if (goal["properties"]["uuid"]["rich_text"] == []):
        goal = origin_notion.pages.update(
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


# Fetch goals from foreign
foreign_primary_key = "Goal Name"
foreign_due_date = "Target Due"
foreign_owner = "Owner"
foreign_owner_id = "b8040e74-2b71-4855-8714-aea4a92ffab8"

foreign_goals = [    
    goal for goal in foreign_notion.databases.query(database_id=os.environ["TABLE_ID_B"])["results"]
    if foreign_due_date in goal["properties"]
    and goal["properties"][foreign_owner]["people"][0]['id'] == foreign_owner_id    
    and today - margin <= parse(goal["properties"][foreign_due_date]["date"]["start"]).date() <= today + margin
]

# Update foreign goals if matched on uuid, otherwise add new goals 
for origin_goal in origin_goals:
    exists_in_foreign = False

    for foreign_goal in foreign_goals:
        if ( "uuid" in foreign_goal["properties"]
        and foreign_goal["properties"]["uuid"]["rich_text"] != []
        and origin_goal["properties"]["uuid"]["rich_text"][0]["text"]["content"]
        == foreign_goal["properties"]["uuid"]["rich_text"][0]["text"]["content"]):            
            update_payload = {"page_id": foreign_goal["id"], "properties":{}}
            update_payload["properties"][foreign_primary_key] = {
                "title": [{
                    "text":{
                        "content": origin_goal["properties"][origin_primary_key]["title"][0]["text"]["content"]
                    }
                }]
            }
            if "Due" in origin_goal["properties"]:
                update_payload["properties"][foreign_due_date] = {
                    "date": {
                        "start": origin_goal["properties"][origin_due_date]["date"]["start"]
                    }                        
                }
            if "Display" in origin_goal["properties"]: 
                update_payload["properties"]["Category"] = {
                    "select": {
                        "name": origin_goal["properties"]["Display"]["select"]["name"] 
                    }
                }
            if "Accomplished" in origin_goal["properties"] and "date" in origin_goal["properties"]["Accomplished"]: 
                update_payload["properties"]["Status"] = {
                    "select": {
                        "name": "Success"
                    }
                }
            if "Weeks Pushed" in origin_goal["properties"]: 
                update_payload["properties"]["Weeks Pushed"] = {
                    "number": origin_goal["properties"]["Weeks Pushed"]["number"]
                }             
            foreign_notion.pages.update(**update_payload)
            exists_in_foreign = True

    if (not exists_in_foreign):
        create_payload = {"parent": {"database_id": os.environ["TABLE_ID_B"]}, "properties":{}}
        create_payload["properties"][foreign_primary_key] = {
            "title": [{                
                "text": {
                    "content": origin_goal["properties"][origin_primary_key]["title"][0]["text"]["content"]                                
                }
            }]
        }        
        create_payload["properties"]["uuid"] = {
            "rich_text": [{
                "type": "text",
                "text": {
                    "content": origin_goal["properties"]["uuid"]["rich_text"][0]["text"]["content"]                                
                }
            }]
        }
       
        create_payload["properties"]["Owner"] = {
            "people": [{
                "object": "user",   
                "id": foreign_owner_id
            }]
        }

        if "Due" in origin_goal["properties"]:
            create_payload["properties"][foreign_due_date] = {
                "date": {
                    "start": origin_goal["properties"][origin_due_date]["date"]["start"]
                }                        
            }
        if "Display" in origin_goal["properties"]: 
            create_payload["properties"]["Category"] = {
                "select": {
                    "name": origin_goal["properties"]["Display"]["select"]["name"] 
                }
            }
        if "Accomplished" in origin_goal["properties"] and "date" in origin_goal["properties"]["Accomplished"]: 
            create_payload["properties"]["Status"] = {
                "select": {
                    "name": "Success"
                }
            }
        if "Weeks Pushed" in origin_goal["properties"]: 
            create_payload["properties"]["Weeks Pushed"] = {
                "number": origin_goal["properties"]["Weeks Pushed"]["number"]
            } 

        foreign_notion.pages.create(
            **create_payload
        )    
