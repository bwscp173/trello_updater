import time
import datetime
import json
import requests

with open("../trelloAPI.json","r") as f:
  trello_data = json.load(f)
with open("../githubAPI.json","r") as f:
  github_data = json.load(f)

TRELLO_API = trello_data["TRELLO_APIKEY"]
TRELLO_TOKEN = trello_data["TRELLO_TOKEN"]
TRELLO_ID_BOARD = trello_data["TRELLO_ID_BOARD"]
BOARD_NAME = 'github-testing'
TRELLO_LIST = f"projectEuler push history"

GITHUB_USERNAME = github_data["GITHUB_USERNAME"]
GITHUB_PASSWORD = github_data["GITHUB_PASSWORD"]
GITHUB_TOKEN = github_data["GITHUB_TOKEN"]
GITHUB_PROJECTNAME = "projectEuler"

class RequestInvalid(Exception):
  def __init__(self, errorMessage):
    super().__init__(errorMessage)

def get_time() -> str:
  """returns yy:mm:dd hr:min:sec
  will be used for logging."""
  return str(datetime.datetime.now())[:-7]

def display_all_id_board():
  url = "https://api.trello.com/1/members/me/boards"

  query = {'key': TRELLO_API,'token': TRELLO_TOKEN,'fields': 'name,id'}

  response = requests.get(url, params=query)

  boards = response.json()

  for board in boards:
      print(f"{board['name']} -> {board['id']}")

def create_new_list(listName: str = "push history"):
  """have a guess what this function does"""
  url = "https://api.trello.com/1/lists"

  query = {'name': listName,'idBoard': TRELLO_ID_BOARD,'key': TRELLO_API,'token': TRELLO_TOKEN}

  response = requests.request("POST",url,params=query)
  if response.status_code == 200:
    print(f"[{get_time()}]successfully added list '{listName}'")
  else:
    raise RequestInvalid(f"Invalid request sent, status code: {response.status_code}")

def get_all_lists():
  url = f"https://api.trello.com/1/boards/{TRELLO_ID_BOARD}/lists"

  query = {
      'key': TRELLO_API,
      'token': TRELLO_TOKEN,
      'fields': 'name'
  }

  response = requests.request(
    "GET",
    url,
    params=query
  )
  if response.status_code == 200:
    return response.json()
  else:
    raise RequestInvalid(f"Invalid request sent, status code: {response.status_code}")

def check_list_exists(listName: str = "push history") -> bool | str:
  """given a lists name will iterate through all list names and return if its found"""
  try:
    responses = get_all_lists()
    print(f"[{get_time()}]request to get all lists succeeded")
  except RequestInvalid as ex:
    print(f"[{get_time()}]request to get all lists failed")
    print(ex)
    return False

  for res in responses:
    if 'name' in list(res.keys()) and 'id' in list(res.keys()):
      if res["name"] == listName:
        return res["id"]
    else:
      raise RequestInvalid("there is a malformed packet being sent from the server, it does not have the 'name' or 'id' key.")
  return False

def create_new_card(idList: str, user,description: str, push_date: str):
  """
  the title of the card will always be the time of the function call with the user appended

  description will show when you click

  example idList is '6810f1275ace42ee8ca3b6db' or '6810ef7b6c46693d6ed9c90c'."""
  url = "https://api.trello.com/1/cards"

  headers = {
    "Accept": "application/json"
  }

  query = {'idList': idList,'key': TRELLO_API,'token': TRELLO_TOKEN,'name': push_date + " - " + user,'desc': description}

  response = requests.request("POST",url,headers=headers,params=query)

  if response.status_code != 200:
    raise RequestInvalid(f"create_new_cards response code is not 200: {response.status_code}")

def get_github_history(repoName: str = "") -> bool | list[dict]:
  """returns false if the status code is not 200
  else returns a list[dictionary] with all the history data for the repo"""


  url = f'https://api.github.com/repos/{GITHUB_USERNAME}/{repoName}/commits'

  # Use Basic Auth with your token
  response = requests.get(url, auth=(GITHUB_USERNAME, GITHUB_TOKEN))
  
  if response.status_code == 200:
    return response.json()
  else:
    raise RequestInvalid(f"invalid request info, status code: {response.status_code}")

def check_trello_card(listName: str, push_summary, push_date, push_author):
  """returns true or false based on if the trello card can be found with those values
  push_summary: the title"""
  res = check_list_exists(listName)

  if not res:
    raise RequestInvalid("Cannot find that trello card idk what should happen just ignore ig")

  if type(res) == str:

    url = f"https://api.trello.com/1/lists/{res}/cards"

    headers = {"Accept": "application/json"}

    query = {'key': TRELLO_API,'token': TRELLO_TOKEN}

    response = requests.request("GET",url,headers=headers,params=query)

    if response.status_code != 200:
      raise RequestInvalid (f"error can not find a card with that listName or connection is down, status code: {response.status_code}")

    json_res = json.loads(response.text)
    for response in json_res:
      if 'desc' in list(response.keys()):
        lines = response['desc'].split('\n')

        if lines[1].find(push_author) != -1 and lines[2].find(push_date) != -1 and lines[4].find(push_summary) != -1:
          #when its confirmed that a cards properties match up
          return True
      else:
        raise RequestInvalid("there is a malformed packet being sent from the server, it does not have the 'desc' key.")
  return False

def add_trello_github_history_cards():
  try:
    res = get_github_history(GITHUB_PROJECTNAME)
    print(f"[{get_time()}]request for getting github history succeeded")
  except RequestInvalid as ex:
    print(f"[{get_time()}]request to get all lists failed")
    print(ex)
    return False

  if type(res) == list:
    history = res

    for push in history:
      push_author = push['commit']['author']['name']
      push_date = push['commit']['author']['date'].replace("T"," ")[:-1]  # '2025-03-29T21:53:59Z' -> '2025-03-29 21:53:59'
      push_message = push['commit']["message"]

      if value := not check_trello_card(TRELLO_LIST,push_message.split("\n")[0],push_date,push_author):
        # print("\n"*2)
        # print("="*20)
        # print(f"author: {push_author}")
        # print(f"push date: {push_date}")
        # print(f"push message: {push_message}")
        # print("="*20)

        try:
          res = check_list_exists(f"{GITHUB_PROJECTNAME} push history")
        except RequestInvalid as ex:
          print(f"[{get_time()}]error {ex}")
          continue

        if type(res) == bool and res == False:
          try:
            create_new_list(f"{GITHUB_PROJECTNAME} push history")
            res = check_list_exists(f"{GITHUB_PROJECTNAME} push history")
          except RequestInvalid as ex:
            print(f"[{get_time()}]error {ex}")
            continue
        if type(res) == str:
          # then response is the id of the list
          idList = res
          push_message = f"""
author: {push_author}
push date: {push_date}
push message:
{push_message}"""
          create_new_card(idList, push_author, push_message, push_date)
      print(f"[{get_time()}]is there a card with that info already: {not value}")

# testing adding new card:
# res = check_list_exists("push history")
# if type(res) == bool and res == False:
#   create_new_list()
#   res = check_list_exists("push history")

# if type(res) == str:
#   # then response is the id of the list
#   create_new_card(res, "teammate1", "description be like, hey words")


# testing getting and adding labels:
# check_list_exists()
# print("\n"*3)
# create_new_list()
# print("\n"*3)
# check_list_exists()

if __name__ == "__main__":
  print("▓" * 48)
  print("author: benedict ward")
  print("adds a gitHubs project history to a trello board")
  print("▓"*80)
  print("""▀█▀ █▀█ █▀▀ █░░ █░░ █▀█   ▄▀█ █░█ ▀█▀ █▀█   █▀▀ █▀█ █▀▄▀█ █▀▄▀█ █ ▀█▀
░█░ █▀▄ ██▄ █▄▄ █▄▄ █▄█   █▀█ █▄█ ░█░ █▄█   █▄▄ █▄█ █░▀░█ █░▀░█ █ ░█░""")
  print("▓" * 80)
  t1 = time.time()
  # add_trello_github_history_cards()
  t2 = time.time()
  print(f"time to execute: {t2-t1} seconds")