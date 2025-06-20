    # init_db.py
from auth_utils import create_db, add_token, is_valid_token

create_db()
add_token("mysecrettoken")

print("Database initialized with token: mysecrettoken")
print(is_valid_token("mysecrettoken")) 