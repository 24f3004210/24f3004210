from flask import Flask  # import Flask framework to create web application
from models import db

# creating configuration between app, controller and db model
app=Flask(__name__)     #creating object of the class: instance of the Flask object
                       #  (__name__)   contains (__main__)
app.secret_key = "zia123"
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///emp.sqlite3"       # setting configuration variable using database model and where it is stored
                                                                    # /// ---> we are using relative path

# Initializing database with Flask application
db.init_app(app) # linking db app to flask app

#Application Setup
def setup_app():
    app.app_context().push()  # Giving access of my current app to other modules like controller.py, model.py etc.
    print("EMP setup is done....")

# Routes will be defined in controller.py
# executable of flask
# calling the setup
setup_app()

from controller import *
if __name__=="__main__":
    app.run(debug=True)  #we will run the application in debug mode


# How to create instance
# In wsl terminal go to the project directory and run the following commands
# python3  ----> to go out of the folder
# from app import db
# db.create_all()
# quit()  ----> to exit from python3


# zeroth record is of admin user
# add it through either db browser or python3 terminal