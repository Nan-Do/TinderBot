# TinderBot
This is a bot in the same spirit as the one found in https://github.com/crockpotveggies/tinderbox. Made with the main purpose to learn the several technologies required to create a project like this. It has similiar features (choosing faces using eigenfaces, interaction with the service, automatic chat) as the referenced bot plus a logic engine that can be feeded with rules to select the user and to choose between possible conversations

The source code requires several dependencies:
  Pynder to interact with the tinder api (altough must be heavily patched to be used)
  opencv to handle the eigenfaces
  Jinja2 and webpy to run the web app
  PyDatalog for the logic engine
  textBlob for the natural language detection.
  And several others
  
Most of them are included in the dist-packages. The big ones like opencv must be installed separately for obvious reasons
