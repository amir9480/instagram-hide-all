from instagram_private_api import Client
from instagram_private_api.http import ClientCookieJar
from instagram_private_api.compat import compat_pickle
import json
import os
import getpass
import sys
import warnings
import time

api = None

def list_diff(a, b):
    return [x for x in a if x not in b]


def show_help():
    print("----------------------------------------------------------------------------")
    print("---------------------------- instagram-hide-all ----------------------------")
    print("----------------------------------------------------------------------------")
    print("[https://github.com/amir9480/instagram-hide-all]\n")
    print("Usage:")
    print(sys.argv[0] + " COMMAND\n")
    print("Commands:")
    print(" * fetch: To fetch information from your account. (You should run this before hide/unhide).")
    print(" * hide: Hide your stories from all of your followers.")
    print(" * unhide: Unhide your stories from all of your followers.")
    print(" * reset: Reset to your settings before hide/unhide.")
    print("----------------------------------------------------------------------------")


def file_get_contents(path, flags, is_json=False):
    if os.path.exists(path):
        f = open(path, flags)
        output = f.read()
        f.close()
        if is_json:
            return json.loads(output)
        return compat_pickle.loads(output)
    return None


def file_put_contents(path, flags, content, is_json=False):
    f = open(path, flags)
    if is_json:
        f.write(json.dumps(content, indent=4))
    else:
        f.write(compat_pickle.dumps(content))
    f.close()


def blocked_users():
    global api
    return [item for item in api.blocked_reels().get('users', [])]


def blocked_ids():
    return list(map(lambda i: i['pk'], blocked_users()))


def followers():
    global api
    follower_users = []
    rank_token = api.generate_uuid()
    results = api.user_followers(api.authenticated_user_id, rank_token)
    follower_users.extend(results.get('users', []))
    next_max_id = results.get('next_max_id')
    while next_max_id and len(follower_users) <= 20000:
        results = api.user_followers(api.authenticated_user_id, rank_token, max_id=next_max_id)
        follower_users.extend(results.get('users', []))
        next_max_id = results.get('next_max_id')
    return follower_users


def follower_ids():
    return list(map(lambda i: i['pk'], followers()))


def safe_ids():
    return list_diff(follower_ids(), blocked_ids())


def fetch():
    if os.path.exists("info.json"):
        os.makedirs("backups", exist_ok=True)
        os.rename("info.json", "backups/info-backup-" + time.strftime("%Y-%m-%d-%H-%M-%S") + ".json")
    file_put_contents(
        "info.json",
        "w",
        {
            'blocked': blocked_ids(),
            'safe': safe_ids()
        },
        True
    )
    print("Your information saved in 'info.json'. Keep it safe!")


def hide_all():
    global api
    if os.path.exists("info.json") == False:
        print('Please fetch to get your account information first.')
        exit(1)
    info = file_get_contents('info.json', 'r', True)
    api.set_reel_block_status(safe_ids(), 'block')
    print("All your followers can not see your stories anymore.")


def unhide_all():
    global api
    if os.path.exists("info.json") == False:
        print('Please fetch to get your account information first.')
        exit(1)
    info = file_get_contents('info.json', 'r', True)
    api.set_reel_block_status(blocked_ids(), 'unblock')
    print("All your followers can see your stories now.")


def reset():
    global api
    if os.path.exists("info.json") == False:
        print('Please fetch to get your account information first.')
        exit(1)
    info = file_get_contents('info.json', 'r', True)
    api.set_reel_block_status(info['blocked'], 'block')
    api.set_reel_block_status(info['safe'], 'unblock')
    print("You are now using your preferred settings.")


def main():
    global api
    try:
        api = Client(None, None, settings=file_get_contents("data.bin", "rb"))
    except:
        if os.path.exists("data.bin"):
            os.remove("data.bin")
        username = input('Your username:')
        password = getpass.getpass('Your password:')
        api = Client(username, password)

    warnings.simplefilter("ignore")

    command = sys.argv[1]  if len(sys.argv) >= 2 else None

    if command == 'fetch':
        fetch()
    elif command == 'hide':
        hide_all()
    elif command == 'unhide':
        unhide_all()
    elif command == 'reset':
        reset()
    else:
        show_help()

    if os.path.exists("data.bin") == False:
        file_put_contents("data.bin", "wb", api.settings)


main()
