from steel import Steel
from pprint import pprint
import inspect

try:
    client = Steel(steel_api_key="test")
    print("Steel Client attributes:")
    pprint(dir(client))
    
    print("\nActions available in client.sessions.computer (if inspectable):")
    # This might fail if it's dynamic
    try:
         print(inspect.signature(client.sessions.computer))
    except:
         print("Could not inspect signature")

except Exception as e:
    print(e)
