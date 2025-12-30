from steel import Steel
from pprint import pprint
import inspect

client = Steel(steel_api_key="test")

print("\nDefault attributes of client.sessions:")
pprint(dir(client.sessions))

try:
    print("\nSignature of client.scrape:")
    print(inspect.signature(client.scrape.scrape))
except:
    pass

try:
    print("\nSignature of client.sessions.create:")
    print(inspect.signature(client.sessions.create))
except:
    pass
