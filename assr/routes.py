from flask import render_template,redirect,url_for,flash,session,request
from assr.models import FilteringHistory,User,optionHistory,wordsHistory
from assr.filter import newsWebsiteCrawling as filterWeb,articleCrawling
from assr.forms import FilterDetailsForm,LoginForm,RegisterationForm,UpdateProfileForm
from assr import app,db,bcrypt
from flask_login import login_user,current_user,logout_user,login_required
from sqlalchemy import desc
import time
from requests import Session


'''
this is the routes, here we set all the pages and what flask should response for each user GET requests 
for example : @app.route("/register",methods=["GET","POST"]) mean if user put url in browser www.ourwebsite.com/register then the register page will display for it 
'''

'''
this two methods used for change the link / to * (flask think this / is a route in our website the we should convert it before )
'''
def changeLink(link):
    return link.replace("/","*")

def RestoreLink(link):
    return link.replace("*","/")


'''
this is the route that return(response) home page 
this method return user_home page in case user logged in and global home page in case user not logged in 
'''
@app.route('/')
def home():
    session['links_classify'] = None
    if current_user.is_authenticated:  #in case user is logged in then we display his home and not global home
        return render_template("user_home.html")
    return render_template("home.html")  #in case user isn't logged in we display the global home of the website 

'''
this is the route that return the page of updateProfile 
this method update the profile in db 
'''
@app.route('/updateProfile',methods=["GET","POST"])
@login_required #this help to stop access to this page in case there is no user logged in 
def updateProfile():
    updateForm = UpdateProfileForm()
    if updateForm.validate_on_submit():  #when user make update then we updated in db (validate check if all entere data is correct )
        current_user.firstName = updateForm.firstname.data
        current_user.lastName = updateForm.lastname.data
        current_user.username = updateForm.Username.data
        current_user.email = updateForm.email.data
        current_user.bio = updateForm.bio.data
        db.session.commit() #updated in db 
        flash("Your Profile Has Been Updated Successfully",'text-green-700 font-bold bg-green-200 py-2 rounded shadow dark:border border-green-200') #flash message that mean data updated successfully 
        return redirect(url_for("home")) #display home page 
    elif request.method == "GET":  #in display (before user update)
        updateForm.firstname.data = current_user.firstName
        updateForm.lastname.data = current_user.lastName
        updateForm.Username.data = current_user.username
        updateForm.email.data = current_user.email
        updateForm.bio.data = current_user.bio
    return render_template("updateProfile.html",form=updateForm) #return the updateProfile page with parameter called form (form include the inputs and buttons and validators )

'''
this route return the filteringDetails page 
in this method user entered the url and choose type of filtering, and data (categories/enteredwords)
after start filtering we save the data in db for history page
''' 
@app.route('/filteringDetails',methods=["GET","POST"])
@login_required #this help to stop access to this page in case there is no user logged in 
def FilterPageDetails():
    title="filteringDetails"
    session['links_classify'] = None #in case user enter to make filtering (then we clear the session before )
    form = FilterDetailsForm()
    if form.validate_on_submit():
        # new_user = create_user()
        website_link = form.newsURL.data
        url = changeLink(website_link)
        data_type = "entered_words" if form.filter_type.data == "entered_words" else "category"
        
        new_history = FilteringHistory( #create new object for FilteringHistory table 
            userHistory = current_user,
            websiteURL = website_link,
            data_type = data_type,
            )
        db.session.add(new_history)
        db.session.flush() #we use it now after we add it then flush will help us 

        #after save the history in FilteringHistory table we should save in wordsHistory table or optionHistory table then we make object for them 
        if form.filter_type.data == "entered_words":
            new_words = wordsHistory(
                history_id = new_history.id,
                enterWord_1 = form.enteredWord1.data,
                enterWord_2 = form.enteredWord2.data,
                enterWord_3 = form.enteredWord3.data,
            )
            db.session.add(new_words)

        else: #if choose options
            data_type = "category"
            new_options = optionHistory(
                history_id = new_history.id,
                politics = form.PoliticsOption.data,
                criminal = form.CriminalOption.data,
                sexual = form.SexualOption.data,
                
            )
            db.session.add(new_options)
        db.session.commit() #after we add the row then we do a commit 

        # new_history = FilteringHistory(user_id=1,websiteURL=website_link,status=True,politics=option1,criminal=option2,sexual=option3,enterWord_1=form.enteredWord1.data,enterWord_2=form.enteredWord2.data,enterWord_3=form.enteredWord3.data)
        return redirect(url_for('displayFilteredWebsite',link=url))
    return render_template("filterPage.html",form=form,title=title) 

'''
this route used for return register page 
this method get the data entered in register form and validate them by validators in form 
and if every thing is fine then save in db then return a success message and redirect to login page 
'''
@app.route("/register",methods=["GET","POST"])
def register():
    if current_user.is_authenticated: #check if user logged in 
        return redirect(url_for("home"))
    registerForm = RegisterationForm()
    if registerForm.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(registerForm.password.data).decode('utf-8') #make the password hashed
        user = User( #create a user object 
            firstName = registerForm.firstname.data,
            lastName = registerForm.lastname.data,
            username = registerForm.Username.data,
            email = registerForm.email.data,
            password = hashed_password,
        )
        db.session.add(user)
        db.session.commit() #save and commit in db 
        flash(f"Account created successfully for {registerForm.Username.data}","text-green-700 font-bold bg-green-200 py-2 rounded shadow dark:border border-green-200")
        return redirect(url_for("login")) #display login page after finish successfully the registeration
    return render_template("register.html",form=registerForm)


'''
this route used for return login page 
this method get the data entered in login form compare them with data in db 
if they correct and exist then accept the login and if not then refuse and display error message  
'''
@app.route("/login",methods=["GET","POST"])
def login():
    if current_user.is_authenticated: #check if user logged in 
        return redirect(url_for("home"))
    loginForm = LoginForm()
    if loginForm.validate_on_submit():
        user = User.query.filter_by(email=loginForm.email.data).first() #get user from db by email
        if user and bcrypt.check_password_hash(user.password,loginForm.password.data):  #if user founded in db and password entered equal to password in db 
            login_user(user,loginForm.remember.data) #this method is exist in flask_login (by this method we make a session for user that make login )
            flash("You have been logged in successfully","text-green-700 font-bold bg-green-200 py-2 rounded shadow dark:border border-green-200")
            return redirect(url_for("home"))
        else: #in case password wrong or user not found in db (check if email exist)
            flash("your email or password is wrong,please check again","text-red-700 font-bold bg-red-200 py-2 rounded shadow dark:border border-red-200")
    return render_template("login.html",form=loginForm)

'''
this route used for make a logout 
'''
@app.route("/logout")
def logout():
    session['links_classify'] = None
    logout_user() #this clear the session for user like current_user etc ... 
    return redirect(url_for("home"))

'''
this route return the news website filtered 
display the FilteredWebsite html code in the NewsWebsiteIframe.html (we send the html code as a parameter to the html page )
in this method we send the data entered by user to the filter scripts (filterWeb to a moethod called main)
and it return for us the html code of the page filtered then we display in our html page (inject it in our html page)
'''
@app.route("/displayFilteredWebsite/<link>")
@login_required
def displayFilteredWebsite(link):
    print('iam printing in displayFilteredWebsite')
    link = RestoreLink(link)
    last_history = fetch_last_user_history() #get the last row added in the history table
    newsWebsite_session = create_session_for_Fetching() #make session in requests (to make the requests fast more )
    start_time = time.time() 
    html_code,classify_links = filterWeb(link,last_history,newsWebsite_session) #classify_links include a links of pages and their classify we save in flask session (like cookies)
    end_time = time.time() 
    elapsed_time = end_time - start_time
    print("Filtering time of main page of news website : ",elapsed_time)
    newsWebsite_session.close()
    session['links_classify'] = classify_links #save classify_links in flask session
    return render_template('NewsWebsiteIframe.html',html_code=html_code) #html page returned by filterWeb(filter) we send as parameter and display it 



'''
this route return the articles filtered (when user click in any article in the page)
display the article html code in the ArticleIframe.html (we send the html code as a parameter to the html page )
in this method we send the data entered by user to the filter scripts (article to a method called article)
and it return for us the html code of the page filtered then we display in our html page (inject it in our html page)
'''
@app.route("/displayFilteredArticle/<link>",methods=['GET','POST'])
@login_required
def displayFilteredArticle(link):
    print('iam printing in displayFilteredArticle')
    last_history = fetch_last_user_history() #get the last row added in the history table 
    extracted_link=link
    extracted_link=extracted_link.replace("*","/") 
    classify_links = session.get('links_classify')
    if classify_links is None: #in case links_classifiy not saved in session or something wrong with get
        classify_links={}
    newsWebsite_session = create_session_for_Fetching()
    start_time = time.time()
    html_code,classify_links = articleCrawling(extracted_link,last_history,classify_links,newsWebsite_session)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print("Filtering time of article in the news website : ",elapsed_time)
    newsWebsite_session.close()
    session['links_classify'] = classify_links
    return render_template('ArticleIframe.html',html_code=html_code)


'''
this route return the history page 
in this method the history returned from the last one (newest one) to the old 
its used paginate for divide the data for pages 
'''
@app.route("/history",methods=['GET'])
@login_required #user should be logged in to go to this page (in case user enter in browser www.ourwebsite.com/history when he isn't logged in then he will get error of 401 )
def history():
    session['links_classify'] = None
    page = request.args.get("page", 1, type=int)
    history_data = []
    user_history = FilteringHistory.query.filter_by(user_id=current_user.id).order_by(desc(FilteringHistory.id)).paginate(page=page, per_page=6) #send 6 data per page ,desc mean return in reverse way 
    for entry in user_history.items: #loop for all data fetched from db and create object for each one 
        entry_data = {} #create new object with data
        entry_data['history'] = entry
        if entry.data_type=="category":
            category = optionHistory.query.filter_by(history_id=entry.id).first() #go to optionHistory and get the row that his history_id is entry.id, first one (without first it will return a list and not just one object)
            entry_data['category']=category
        else:
            entered_words = wordsHistory.query.filter_by(history_id=entry.id).first()
            entry_data['entered_words']=entered_words
        history_data.append(entry_data) #add object to the list 
    return render_template("displayHistory.html",History=history_data,user_history=user_history)


'''
this method get the data from the db the last history of user (history that he entered now)
'''
def fetch_last_user_history():
    # get last history done by the user (the most new one)
    last_history = FilteringHistory.query.filter_by(user_id=current_user.id).order_by(FilteringHistory.id.desc()).first()
    
    if not last_history:
        return None  # in case not found last_History return none

    # in case data is entered_words
    if last_history.data_type == "entered_words":
        words_data = wordsHistory.query.filter_by(history_id=last_history.id).first()
        if words_data:
            enteredwords = [words_data.enterWord_1, words_data.enterWord_2, words_data.enterWord_3]
            enteredwords = [word for word in enteredwords if word] 
            return {'type': 'entered_words', 'data': enteredwords}

    # in case data is categories
    elif last_history.data_type == "category":
        options_data = optionHistory.query.filter_by(history_id=last_history.id).first()
        if options_data:
            options = {
                'politics': options_data.politics,
                'criminal': options_data.criminal,
                'sexual': options_data.sexual,
            }
            return {'type': 'category', 'data': options}

    #in case there is no data
    return None



'''
this pages is a error pages 
'''
@app.errorhandler(401)
def error_401(error):
    return render_template('401.html'),401
@app.errorhandler(403)
def error_403(error):
    return render_template('403.html'),403
@app.errorhandler(404)
def error_404(error):
    return render_template('404.html'),404
@app.errorhandler(500)
def error_500(error):
    return render_template('500.html'),500


'''
this is setting and configrations for session for requests library 
this headers and setting help the seasson still open after make requests (help us for fasting the filtering process and fetch pages )
'''
def create_session_for_Fetching():
    session = Session()
    #this string will save in cookies and help the news website server know that the connection should be openened because we will fetch more data 
    #you can see here scraping using like this string : https://medium.com/@19emilabos/scrape-business-emails-from-instagram-using-python-d1f2386ea665
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3' 
    })
    return session


