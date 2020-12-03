from minimums import * 
from flask import Flask, render_template, request, url_for, flash, redirect

application = Flask(__name__)
application.config['SECRET_KEY'] = 'SKNJAFI4O49RONAERVKJNAFV9J430249KMRWFVOIW'


@application.route('/', methods = ['POST','GET'])
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

if __name__ == "__main__":
    application.run(port=5000, debug=True)
