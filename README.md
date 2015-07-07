# TinderBot
This is a bot in the same spirit as the one found in https://github.com/crockpotveggies/tinderbox. Made just for fun. It has the similiar features (choosing faces using eigenfaces, interaction with the service, automatic chat) plus a logic engine that can be feeded with rules to select the user and to choose between possible conversations

The source code requires several dependencies:
  Pynder to interact with the tinder api (altough must be heavily patched to be used)
  opencv to handle the eigenfaces
  Jinja2 and webpy to run the web app
