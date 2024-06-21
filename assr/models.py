
from assr import db,Login_manger
from flask_login import UserMixin #this import get us 4 method (is_authinticated,is_active,is_anonymos,get_userID) this mean this help us in checking details about user that is login 
from datetime import datetime

'''
this is the models, its used for create the tables in db 
sqlAlchemy used it for create the tables 
'''

'''
when user make login then we get the data from the db about the user and save it (this help us for check if user loggedin and authintications)
'''
@Login_manger.user_loader
def load_user(user_id):
     return User.query.get(int(user_id)) #int to verify that we use id as integer

'''
this is the user table, its include some fields like username,email,id etc...
'''
#multi inhertance 
class User(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True) #id is primary key 
    username = db.Column(db.String(100),unique=True,nullable=False)
    firstName = db.Column(db.String(100),nullable=False) #nullable=False mean this field can be empty or not filled 
    lastName = db.Column(db.String(100),nullable=False)
    profileIMG = db.Column(db.String(20),nullable=False,default="defaultUserPhoto.png")
    email = db.Column(db.String(100),unique=True,nullable=False) #unique to not giving more than one user register with same email
    password = db.Column(db.String(60),nullable=False)
    bio = db.Column(db.Text,nullable=True)
    history = db.relationship('FilteringHistory',backref='userHistory',lazy=True)  #we have relationship with filteringHistory one for many
    def __repr__(self):
        return f"User('{self.firstName}','{self.lastName}','{self.username}','{self.email}')"
    
'''
this is the filterHistory table, its include some fields like user_id,entered data,id etc...
this table store the history of filtering done by user 
user_id help us to know that the row in this table belong to him (its foriegn key because its belong to user table )
'''
class FilteringHistory(db.Model):
        id = db.Column(db.Integer,primary_key=True)
        user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
        date_created = db.Column(db.DateTime,nullable=False, default=datetime.utcnow)
        websiteURL = db.Column(db.String(100), nullable=False)
        data_type = db.Column(db.String(25), nullable=False) #here we save datatype user entred (choose options or entered words)
        option_history = db.relationship('optionHistory',backref='history',lazy=True)
        words_history = db.relationship('wordsHistory',backref='history',lazy=True) #relationship one to one with words_history 


'''
this is the optionHistory Table, we store in it the history of categories choosed by the user
it is in realtionship with filteringHistory 
'''
class optionHistory(db.Model):
    id = db.Column(db.Integer,primary_key=True) #set as primary key 
    history_id = db.Column(db.Integer,db.ForeignKey('filtering_history.id'),nullable=False) #set as foreignkey in filtering history table
    politics = db.Column(db.Boolean, nullable=True)
    criminal = db.Column(db.Boolean, nullable=True) #nullable=true mean this field can be null(empty )
    sexual = db.Column(db.Boolean, nullable=True)


'''
this is the wordsHistory Table, we store in it the history of words entered by the user
it is in realtionship with filteringHistory 
'''
class wordsHistory(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    history_id = db.Column(db.Integer,db.ForeignKey('filtering_history.id'),nullable=False) #this is foriegnkey for filteringHistory table
    enterWord_1 = db.Column(db.String(25), nullable=True)
    enterWord_2 = db.Column(db.String(25), nullable=True)
    enterWord_3 = db.Column(db.String(25), nullable=True) #word length can be max 25 chars


