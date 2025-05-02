import time
import datetime
import json
import requests
from pyasn1.debug import Printer

with open("../trelloAPI.json","r") as f:
  trello_data = json.load(f)
with open("../githubAPI.json","r") as f:
  github_data = json.load(f)

TRELLO_API = trello_data["TRELLO_APIKEY"]
TRELLO_TOKEN = trello_data["TRELLO_TOKEN"]
TRELLO_IDBOARD = trello_data["TRELLO_IDBOARD"]
BOARD_NAME = 'github-testing'
TRELLO_LIST = f"projectEuler push history"

GITHUB_USERNAME = github_data["GITHUB_USERNAME"]
GITHUB_PASSWORD = github_data["GITHUB_PASSWORD"]
GITHUB_TOKEN = github_data["GITHUB_TOKEN"]
GITHUB_PROJECTNAME = "projectEuler"

def DisplayAll_idBoard():
  url = "https://api.trello.com/1/members/me/boards"

  query = {
      'key': TRELLO_API,
      'token': TRELLO_TOKEN,
      'fields': 'name,id'
  }

  response = requests.get(url, params=query)

  boards = response.json()

  for board in boards:
      print(f"{board['name']} -> {board['id']}")

def CreateNewList(listName: str = "push history"):
  """have a guess what this function does"""
  url = "https://api.trello.com/1/lists"

  query = {
    'name': listName,
    'idBoard': TRELLO_IDBOARD,
    'key': TRELLO_API,
    'token': TRELLO_TOKEN
  }

  response = requests.request(
    "POST",
    url,
    params=query
  )
  match response.status_code:
    case 200:
      print("sucessfully added list '{listName}'")
  print(response)

def GetAllLists():
  url = f"https://api.trello.com/1/boards/{TRELLO_IDBOARD}/lists"

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
    print("Invalid request sent, status code " + response.status_code)
    return [{"name":"Invalid request IGNORE"}]

def CheckListExists(listName: str = "push history") -> bool | str:
  """given a lists name will iterate through all list names and return if its found"""
  response = GetAllLists()
  for list in response:
    if list["name"] == listName:
      return list["id"]
  return False

def CreateNewCard(idList: str, user,description: str, push_date: str):
  """
  the title of the card will always be the time of the function call with the user appended

  description will apear when you click

  example idList is '6810f1275ace42ee8ca3b6db' or '6810ef7b6c46693d6ed9c90c'."""
  url = "https://api.trello.com/1/cards"

  headers = {
    "Accept": "application/json"
  }

  query = {
    'idList': idList,
    'key': TRELLO_API,
    'token': TRELLO_TOKEN,
    'name': push_date + " - " + user,
    'desc': description
  }

  response = requests.request(
    "POST",
    url,
    headers=headers,
    params=query
  )

  if response.status_code != 200:
    print("CreateNewCards response code isnt 200: ", response.text)

  #print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))

def GetGitHubHistory(repoName: str = "") -> bool | list[dict]:
  """returns false if the status code is not 200
  else returns a list[dictionary] with all the history data for the repo"""


  url = f'https://api.github.com/repos/{GITHUB_USERNAME}/{repoName}/commits'

  # Use Basic Auth with your token
  response = requests.get(url, auth=(GITHUB_USERNAME, GITHUB_TOKEN))
  
  if response.status_code == 200:
    return response.json()
    
  print(response.status_code)

def CheckTrelloCard(listName: str, pushsummary, pushdate, pushauthor):
  """returns true or false based on if the a trello card can be found with those values
  pushsummary: the title"""
  res = CheckListExists(listName)

  if not res:
    raise Exception("Cannot find that trello card idk what should happen just ignore ig")

  if type(res) == str:

    url = f"https://api.trello.com/1/lists/{res}/cards"

    headers = {
      "Accept": "application/json"
    }

    query = {
      'key': TRELLO_API,
      'token': TRELLO_TOKEN
    }

    response = requests.request(
      "GET",
      url,
      headers=headers,
      params=query
    )

    if response.status_code != 200:
      raise Exception ("error can not find a card with that listName or connection is down")

    json_res = json.loads(response.text)
    for response in json_res:
      lines = response['desc'].split('\n')

      # for i in range(len(lines)):
      #   print(f"line{i}: {lines[i]}")

      if lines[1].find(pushauthor) != -1 and lines[2].find(pushdate) != -1 and lines[4].find(pushsummary) != -1:
        #when its confirmed that a cards properties match up
        return True
  return False

def AddTrelloGitHubHistoryCards():
  res = GetGitHubHistory(GITHUB_PROJECTNAME)
  if type(res) == list:
    history = res


    for push in history:
      push_author = push['commit']['author']['name']
      push_date = push['commit']['author']['date'].replace("T"," ")[:-1]  # '2025-03-29T21:53:59Z' -> '2025-03-29 21:53:59'
      push_message = push['commit']["message"]


      if value := not CheckTrelloCard(TRELLO_LIST,push_message.split("\n")[0],push_date,push_author):
        print("\n"*2)
        print("="*20)
        print(f"author: {push_author}")
        print(f"push date: {push_date}")
        print(f"push message: {push_message}")
        print("="*20)


        res = CheckListExists(f"{GITHUB_PROJECTNAME} push history")
        if type(res) == bool and res == False:
          CreateNewList(f"{GITHUB_PROJECTNAME} push history")
          res = CheckListExists(f"{GITHUB_PROJECTNAME} push history")

        if type(res) == str:
          # then response is the id of the list
          idList = res
          push_message = f"""
author: {push_author}
push date: {push_date}
push message:
{push_message}"""
          CreateNewCard(idList, push_author, push_message, push_date)
      print("is there a card with that info already: ", not value)

#print("did it find anything: ", CheckTrelloCard(TRELLO_LIST,"Initial commit","2025-03-24 21:29:14","bwscp173"))
AddTrelloGitHubHistoryCards()

# testing adding new card:
# res = CheckListExists("push history")
# if type(res) == bool and res == False:
#   CreateNewList()
#   res = CheckListExists("push history")

# if type(res) == str:
#   # then response is the id of the list
#   CreateNewCard(res, "teammate1", "description be like, hey words")


# testing getting and adding labels:
# CheckListExists()
# print("\n"*3)
# CreateNewList()
# print("\n"*3)
# CheckListExists()