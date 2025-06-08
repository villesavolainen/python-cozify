#!/usr/bin/env python3
from cozify import hub, cloud
import sys
import pprint

def main(capability=None):
    users = hub.users()
    print(users)
    print("All users:")
    for userid, user_data in users.items():
        # Extract user info from the nested structure
        user_info = user_data.get('user_info', {})
        user = user_info.get('user', {})

        # Get user details
        nickname = user.get('nickname', 'Unknown')
        email = user.get('email', 'Unknown')
        phone = user.get('phone', 'None')
        role = user_info.get('role', 'Unknown')

        # Get connection status
        connected = user_data.get('connected', False)
        revoked = user_data.get('revoked', False)

        status = "Connected" if connected else "Disconnected"
        if revoked:
            status += " (Revoked)"

        print(f"ID: {userid}")
        print(f"  Nickname: {nickname}")
        print(f"  Email: {email}")
        print(f"  Phone: {phone}")
        print(f"  Role: {role}")
        print(f"  Status: {status}")
        print("")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
