from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('login.html')
#Mirar SQLAlchemy ORM

@app.route('/wallet')
def wallet():
    return render_template('tab1cartera.html', title = 'Cartera')

@app.route('/getcoins')
def getcoins():
    return render_template('tab2get.html')

@app.route('/offers')
def coins():
    return render_template('tab3offers.html')
# def login():
#     error =None
#     if request.method == 'POST':
#         if valid_login(request.form['username'], request.form['password']):
#             return log_the_user_in(request.form['username'])
#         else:
#             error = 'Invalid username or password'
#     return render_template('login.html', error=error)
if __name__ == "__main__":
    app.run(debug=True)