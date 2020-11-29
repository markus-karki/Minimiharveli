from minimums import * 
from flask import Flask, render_template, request, url_for, flash, redirect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SKNJAFI4O49RONAERVKJNAFV9J430249KMRWFVOIW'


@app.route('/', methods = ['POST','GET'])
def index():
   
    if request.method == 'POST':
        departure = request.form['departure']
        destination = request.form['destination']
        alternate = request.form['alternate']

        minimums(departure, destination, alternate)
        
        f = open('solution.txt') 
        content = f.read()
        f.close() 
        return render_template("solution.html", text=content)

    return render_template('index.html')
