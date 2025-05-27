import time
import datetime
import json
import requests

with open("trelloAPI.json","r") as f:
  trello_data = json.load(f)
with open("githubAPI.json","r") as f:
  github_data = json.load(f)

TRELLO_API = trello_data["TRELLO_APIKEY"]
TRELLO_TOKEN = trello_data["TRELLO_TOKEN"]
TRELLO_ID_BOARD = trello_data["TRELLO_ID_BOARD"]  # use the function 'display_all_id_board()' to get the full idboard 

GITHUB_USERNAME = github_data["GITHUB_USERNAME"]
GITHUB_TOKEN = github_data["GITHUB_TOKEN"]  # a general token for public repos
GITHUB_PRIVATE_TOKEN = github_data["GITHUB_PRIVATE_REPO_TOKEN"]  # for set privated repos
GITHUB_PROJECTNAME = "CMP-Y1-synoptic-project"  # has to be the githubs repos name
TRELLO_LIST = f"{GITHUB_PROJECTNAME} push history"  # list name on trello
use_github_private_token = True  # CHANGE THIS, when a fetch request fails i will swap this value and try again.

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

  query = {'name': listName, 'idBoard': TRELLO_ID_BOARD, 'key': TRELLO_API, 'token': TRELLO_TOKEN}

  response = requests.request("POST",url,params=query)
  if response.status_code == 200:
    print(f"[{get_time()}]successfully added list '{listName}'")
  else:
    raise RequestInvalid(f"Invalid request sent, status code: {response.status_code}")

def get_all_lists() -> requests.Response:
  url = f"https://api.trello.com/1/boards/{TRELLO_ID_BOARD}/lists"

  query = {'key': TRELLO_API,'token': TRELLO_TOKEN,'fields': 'name'}

  response = requests.request("GET",url,params=query)

  if response.status_code == 200:
    return response.json()
  else:
    raise RequestInvalid(f"Invalid request sent, status code: {response.status_code}")

def check_list_exists(listName: str = "push history", all_lists:list[dict]  = []) -> bool | str:
  """returns False if not found, else returns listId
  given a lists name will iterate through all list names and return if its found
  a listId example should look like '68320c9651d609bc030e3f11'.
  
  you can parse in the result from 'get_all_lists()' to save resources"""
  if all_lists == []:
    try:
      all_lists = get_all_lists()
      print(f"[{get_time()}]request to get all lists succeeded")
    except RequestInvalid as ex:
      print(f"[{get_time()}]request to get all lists failed")
      print(ex)
      return False

  for res in all_lists:
    if 'name' in list(res.keys()) and 'id' in list(res.keys()):
      if res["name"] == listName:
        return res["id"]
    else:
      raise RequestInvalid("there is a malformed packet being sent from the server, it does not have the 'name' or 'id' key.")
  return False

def create_new_card(idList: str, branch:str, user:str, description: str, push_date: str):
  """
  the title of the card will always be the time of the function call with the user appended

  description will show when you click

  example idList is '6810f1275ace42ee8ca3b6db' or '6810ef7b6c46693d6ed9c90c'."""
  url = "https://api.trello.com/1/cards"

  headers = {
    "Accept": "application/json"
  }

  trello_title = f"{branch} - {user} - {push_date}"
  query = {'idList': idList,'key': TRELLO_API,'token': TRELLO_TOKEN,'name': trello_title,'desc': description}

  response = requests.request("POST",url,headers=headers,params=query)

  if response.status_code != 200:
    raise RequestInvalid(f"create_new_cards response code is not 200: {response.status_code}")
  print(f"[{get_time()}]created new card titled '{trello_title}'")

def get_branch_history(repo_name: str) -> list[list[str, str, str, str]]:
  """will return a list of all commits to all branches on a github project.
  will return -> [[branch_name, author, date, message]]"""
  token = GITHUB_TOKEN
  if use_github_private_token:
    token = GITHUB_PRIVATE_TOKEN

  headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
  }
  branches_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/branches"
  response = requests.get(branches_url, headers=headers)

  if response.status_code != 200:
    raise RequestInvalid(f"invalid request info, status code: {response.status_code}")

  branches = response.json()
  all_github_history = []
  
  for branch in branches:
      branch_name = branch['name']
      print(f"\nCommits for branch: {branch_name}")
      
      commits_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/commits?sha={branch_name}"
      commits_response = requests.get(commits_url, headers=headers)

      if commits_response.status_code != 200:
        raise RequestInvalid(f"invalid request info, status code: {commits_response.status_code}")
      
      commits = commits_response.json()

      for commit in commits:
          commit["branch"] = branch_name
          all_github_history.append(commit)

  print(f"[{get_time()}]got all commits from all branches")
  return all_github_history

def get_github_history(repoName: str = "") -> list[dict]:
  """please use 'get_branch_history()' instead of this function. its actually does something about branches
  returns a list[dictionary] with all the history data for the repo
  i havent fully checked what happens when the response is empty, it just returns the json."""

  url = f'https://api.github.com/repos/{GITHUB_USERNAME}/{repoName}/commits'

  token = GITHUB_TOKEN
  if use_github_private_token:
    token = GITHUB_PRIVATE_TOKEN

  response = requests.get(url, auth=(GITHUB_USERNAME, token))
  
  if response.status_code == 200:
    return response.json()
  else:
    raise RequestInvalid(f"invalid request info, status code: {response.status_code}")

def check_trello_card(listName: str, branch, push_summary, push_date, push_author):
  """returns true or false based on if the trello card can be found with those values
  push_summary: the title"""
  res = check_list_exists(listName)  # this line is responsible for the 2 sets of getting lists

  if res == False:
    raise RequestInvalid(f"Cannot find trello card with the name '{listName}' idk what should happen just ignore ig")

  if type(res) == str and len(res) == 24:

    url = f"https://api.trello.com/1/lists/{res}/cards"
    headers = {"Accept": "application/json"}
    query = {'key': TRELLO_API,'token': TRELLO_TOKEN}
    response = requests.request("GET", url, headers=headers, params=query)

    if response.status_code != 200:
      raise RequestInvalid (f"error can not find a card with that listName or connection is down, status code: {response.status_code}")

    json_res = json.loads(response.text)
    for response in json_res:
      if 'desc' in list(response.keys()):
        lines = response['desc'].split('\n')

        #not going to check for the branch as it will create a copy of the main history
        if lines[2].find(push_author) != -1 and lines[3].find(push_date) != -1 and lines[5].find(push_summary) != -1:
          #when its confirmed that a cards properties match up
          return True
      else:
        raise RequestInvalid("there is a malformed packet being sent from the server, it does not have the 'desc' key.")
  return False

def add_trello_github_history_cards(list_name:str = "push history"):
  #i know this function is too long i will eventually get round to shortening it
  try:
    history = get_branch_history(GITHUB_PROJECTNAME)
    print(f"[{get_time()}]request for getting github history succeeded")
  except RequestInvalid as ex:
    print(f"[{get_time()}]request to get all branches commit history failed")
    print(ex)
    return False
  
  history_starting_at_main = []
  # this is going to mess up the big O notation for the project.
  # there HAS to be a better way for this im just getting sleepy
  for push in history:
    if push["branch"] == "main":
      history_starting_at_main.append(push)

  for push in history:
    if push["branch"] != "main":
      history_starting_at_main.append(push)

  for push in history_starting_at_main:
    #i know this if satement is long, its just checking if the keys exit
    if 'commit' in list(push.keys()) and 'branch' in list(push.keys()) and 'author' in list(push['commit'].keys()) and 'date' in list(push['commit']['author'].keys()) and 'message' in list(push['commit'].keys()):
      push_author = push['commit']['author']['name']
      push_date = push['commit']['author']['date'].replace("T"," ")[:-1]  # '2025-03-29T21:53:59Z' -> '2025-03-29 21:53:59'
      push_message = push['commit']["message"]
      push_branch = push['branch']
      
      #if it cant get the list then create it, if it gets a valid response but without 'list_name' then create_new_list
      try:
        list_exist = check_list_exists(list_name)
      except:
        create_new_list(list_name)
        list_exist = True

      if list_exist == False:
        create_new_list(list_name)

      all_lists = get_all_lists()
      does_not_exist = not check_trello_card(list_name, push_branch, push_message.split("\n")[0], push_date,push_author)
      print(f"[{get_time()}]is there a card with that info already: {not does_not_exist}")
      if does_not_exist:  # rip walrus operator used on this line you will be missed.
        try:
          res = check_list_exists(list_name, all_lists)
        except RequestInvalid as ex:
          print(f"[{get_time()}]error {ex}")
          continue

        # needs both the type check and == false as if res is a str, then it will error when it checks false
        # but if its a str it will fail the first condition and skip the 2nd
        while type(res) == bool and res == False:
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
branch: {push_branch}
author: {push_author}
push date: {push_date}
push message:
{push_message}"""
          create_new_card(idList, push_branch, push_author, push_message, push_date)
    else:
      raise RequestInvalid(f"request received by the server is malformed, can not find either 'commit' 'author' 'date' ''")

def display_credits():
  print("▓" * 48)
  print("author: benedict ward")
  print("description: adds a gitHubs project history to a trello board")
  print("notes: pretty please ignore any spelling mistakes, dyslexia am i right?")

  print("▓"*81)
  print("""\n     ▀█▀ █▀█ █▀▀ █   █   █▀█   ▄▀█ █ █ ▀█▀ █▀█   █▀▀ █▀█ █▀▄▀█ █▀▄▀█ █ ▀█▀
      █  █▀▄ ██▄ █▄▄ █▄▄ █▄█   █▀█ █▄█  █  █▄█   █▄▄ █▄█ █ ▀ █ █ ▀ █ █  █ \n""")
  print("▓" * 81)


if __name__ == "__main__":
  display_credits()

  start_time = time.time()
  add_trello_github_history_cards(f"{GITHUB_PROJECTNAME} push history")
  end_time = time.time()

  time_to_run = str(end_time-start_time)
  print(f"time to execute: {time_to_run[:time_to_run.find(".")+3]} seconds")