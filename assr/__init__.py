from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_login import LoginManager


app = Flask(__name__)
app.config['SECRET_KEY'] = "this_is_my_secret_key_when_finish_replace_it"

# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/dbfortesting'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/websitefilterdb'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///websiteFilteringDB'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dbfortesting'


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.app_context().push()
migrate = Migrate(app, db)
bcrypt = Bcrypt(app) # get a object from Bcrypt (for bycrpt password when save in db)
Login_manger = LoginManager(app)

#global Variables 


from assr import routes