from flask_wtf import FlaskForm
from wtforms import StringField,URLField,BooleanField,SubmitField,PasswordField,RadioField,TextAreaField
from wtforms.validators import DataRequired,URL,Length,Email,EqualTo,ValidationError
from assr.models import User
from flask_login import current_user

'''
this is the forms, it used in each page include a data the user should fill for example 
in login page he should enter his email,password , in filterDetails page it should enter the data about filtering like url of page and categories/entered words 
this forms help us to validate the input data (its include a VALIDATORS prepared in advance )
'''

'''
this form used in filterDetails page, it have a input of URL and RADIO BUTTON about type of the filter (category/entered_words)
checkbox for category fields and input (text) for entered words and submit button 
each one have validators for example some have max length that user can enter 
'''
class FilterDetailsForm(FlaskForm):
    newsURL = URLField('NewsWebsite URL',validators=[DataRequired(),Length(max=100)])
    filter_type = RadioField('choose filtering type:',choices=[('category','category'),('entered_words','entered_words')],validators=[DataRequired()])
    PoliticsOption = BooleanField('Politics')
    CriminalOption = BooleanField('Criminal')
    SexualOption = BooleanField('Sexual')
    enteredWord1 = StringField("word",validators=[Length(max=25)],render_kw={"placeholder": "word1"})
    enteredWord2 = StringField("word",validators=[Length(max=25)],render_kw={"placeholder": "word2"})
    enteredWord3 = StringField("word",validators=[Length(max=25)],render_kw={"placeholder": "word3"})
    Submit = SubmitField('Start Filtering Process')

'''
form in login page, it have 2 inputs (email,password) and submit button
validators like dataRequired mean the input shouldn't be empty and Email() mean the text in input should be emal
'''
class LoginForm(FlaskForm):
    email = StringField('Email:',validators=[DataRequired(),Email()])
    password = PasswordField('Password:',validators=[DataRequired()])
    remember = BooleanField('Remember Me!!')
    submit = SubmitField('Login')

'''
form in register page, it have 6 inputs and submit button
validators like dataRequired mean the input shouldn't be empty and Email() mean the text in input should be emal
'''
class RegisterationForm(FlaskForm):
    firstname=StringField('First Name: ',validators=[DataRequired(),Length(min=2,max=25)])
    lastname=StringField('Last Name: ',validators=[DataRequired(),Length(min=2,max=25)])
    Username=StringField('Username: ',validators=[DataRequired(),Length(min=2,max=25)])
    email = StringField('Email: ',validators=[DataRequired(),Email()])
    password = PasswordField('Password:',validators=[DataRequired(),Length(min=8,max=25)])
    confirm_password = PasswordField('Confirm Password:',validators=[DataRequired(),EqualTo('password')]) #equalTo mean it should equal to the data entere din password input 
    submit = SubmitField('Register')

    '''
    this is a validate for check if username is exist in db 
    '''
    def validate_Username(self,Username):
        user = User.query.filter_by(username=Username.data).first() #by sqlachemy we check if this username exist in db 
        if user: 
            raise ValidationError("Username already exist, Please choose another one!!!") 
    
    '''
    this is a validate for check if email is exist in db 
    '''
    def validate_email(self,email):
        user = User.query.filter_by(email=email.data).first()  #trying to get user with this email if founded mean there is user with this email exist 
        if user: 
            raise ValidationError("Email already exist, Please choose another one!!!") #in case its exist then send this error message 


'''
form in updateProfile page, it have 5 inputs and submit button
validators like dataRequired mean the input shouldn't be empty and Email() mean the text in input should be emal
'''
class UpdateProfileForm(FlaskForm):
    firstname=StringField('First Name: ',validators=[DataRequired(),Length(min=2,max=25)])
    lastname=StringField('Last Name: ',validators=[DataRequired(),Length(min=2,max=25)])
    Username=StringField('Username: ',validators=[DataRequired(),Length(min=2,max=25)])
    email = StringField('Email: ',validators=[DataRequired(),Email()])
    bio = TextAreaField("Bio:")
    submit = SubmitField('Update Profile')

    '''
    validator for check if the update username is exist in db 
    '''
    def validate_Username(self,Username):
        if Username.data != current_user.username: 
            user = User.query.filter_by(username=Username.data).first()
            if user: 
                raise ValidationError("Username already exist, Please choose another one!!!")
    '''
    validator for check if the update email is exist in db 
    '''
    def validate_email(self,email):
        if email.data != current_user.email: 
            user = User.query.filter_by(email=email.data).first()  #trying to get user with this email if founded mean there is user with this email exist 
            if user: 
                raise ValidationError("Email already exist, Please choose another one!!!")