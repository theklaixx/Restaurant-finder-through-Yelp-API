from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime
import json, requests 
import os
import secrets

#____ CONFIGURATIONS:
# creates an instance of the Flask Class. 
app = Flask(__name__)

# Links SQLAlchemy to use an SQLite database named 'SQLite_database.db'.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///SQLite_database.db'
# Create an instance of the SQLAlchemy Class and connects it to the Flasks instance app.
db = SQLAlchemy(app)

#  Access the Yelp API key from the environment variable 'YELP_API_KEY'
Yelp_API_Key = os.environ.get('YELP_API_KEY')

secret_key_= secrets.token_hex(16)
app.secret_key = secret_key_

#____
'''
    Defining the structure of database tables in SQLAlchemy by 
    creating a new Class: UserQuery that inherits from db.Model.
'''
class UserQuery(db.Model):
    
    '''
    The created database has 4 columns:
    - id: a column of type: Integer that stores a Unique Id and acts like a primary key
    - ip_address: a column of type: String for storing the IP address of the user
    - search_query: a column of type: String for storing the query
    - timestamp: a column of type: String for the timestamp that the query was made
    '''

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(15))
    search_query = db.Column(db.String(120))
    timestamp = db.Column(db.String(20))

with app.app_context():
    '''
    Creates the 'SQLite_database.db' file according to the defined model (UserQuery), 
    if it doesn't alreadt exist.
    '''
    db.create_all()

#Decorator: tells Flask that this function should be called on the / URL path of the website. (home page)
@app.route('/') 
def home():
    '''
    Processes and displays the specified page (home.html).
    It translates any templating code written in Jinja2 found in the specified HTML file.
    '''
    return render_template('home.html')

# Decorator: tells Flask that this function should be called only when a POST request
# is made on the /user-search URL path of the website.
@app.route('/user-search', methods=['Post'])
def search():

    # Receives user input from the form. 
    # It is in the form of a dictionary where key is "search_input" and value is the userinput
    user_city = request.form.get('search_input', '')
    # Capitalizes the first letter of each word and removes any extra whitespace
    user_city=user_city.strip().title()
    
    # Receives the IP address of the client that made the request.
    user_ip = request.remote_addr 
    
    # Create a new UserQuery instance
    new_query = UserQuery(ip_address=user_ip, search_query=user_city, timestamp=datetime.now().strftime('%d/%m/%y %H:%M:%S'))
    # Add the new record to the database session and commit it to SQLite DB.
    db.session.add(new_query)
    db.session.commit()

    '''
    End_Point - URL of the Yelp API endpoint for searching businesses.
    Header - Dictionary which includes the authorization header required by the Yelp API
    Params - Dictionary which defines the parameters for the API request.
    '''
    End_Point="https://api.yelp.com/v3/businesses/search"
    Header= { "Authorization": f"Bearer {Yelp_API_Key}"}
    Params = {
        "term": "restaurant",
        "location": user_city,
        "limit": 50
    }

    # Make a request to the Yelp API
    response = requests.get(url=End_Point, params=Params, headers=Header)
    # The API response in JSON format is parsed for easier data extraction
    restaurant_data = response.json()
        # Note: restaurant_data returned from the API has dict_keys(['businesses', 'total', 'region'])

    '''
    Checks if the business key is found within the returned data:
    if so it returns a list of dictionaries, where each dictionary has info about a specific restaurant
    else it returns the appropriate message to the corresponding script (city.html)
    '''
    if "businesses" in restaurant_data:
        restaurants = []
        for restaurant in restaurant_data["businesses"]:
            restaurants.append({
                "name": restaurant["name"],
                "city": restaurant["location"]["city"],
                "rating": restaurant["rating"],
                "url": restaurant["url"]
            })

        return render_template('city.html', restaurants=restaurants, user_city=user_city)
    else:
        # No restaurants found
        return render_template('city.html', message="No restaurants found in " + user_city, user_city=user_city)


# Decorator: tells Flask that this function should be called on the /admin URL path of the website. 
@app.route('/admin') 
def admin_page():
    '''
    Purpose:
    Selects each unique 'search_query' from the 'user_query' table  and counts the number of occurrences for each. 
    It returns a list of tuples.
    If query data is returned and is not empty or None it is sent to the admin html script 
    #else the approrpriat message is sent to the admin html script 
    ''' 
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    sql = text('SELECT search_query, COUNT(*) FROM user_query GROUP BY search_query')

    query_data = db.session.execute(sql).fetchall()

    if query_data:
        return render_template('admin.html',query_data=query_data)
    else:
        return render_template('admin.html',message="No queries found.")
    
# Decorator: tells Flask that this function should be called on the /admin_login URL path of the website. 

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == '123456':
            session['logged_in'] = True
            return redirect('/admin')
        else:
            return render_template('admin_login.html', error_message="YOU HAVE ENETERED WRONG USERNAME OR PASSWORD! <br> PLEASE TRY AGAIN WITH VALID LOGIN DETAILS!")
    return render_template('admin_login.html')


'''
Purpose: 
Runs the app, by checking if the script is being run directly,
hence it is the main program.
'''
if __name__ == '__main__':
    #Starts the Flask web application, by running the instance of Flask
    app.run()  


#____USEFULL LINKS AND COMMANDS____:

#create a VE: python3 -m venv venv
#activate VE:  source venv/bin/activate
#deactivate VE: virtual machine: deactivate
    
#pip install -r requirements.txt

#export YELP_API_KEY="__APIKEY__"
    
# RUN : python app.py
# STOP RUN: Ctrl+C
    
#localhost: http://127.0.0.1:5000

