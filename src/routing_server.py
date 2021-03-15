from flask import Flask
from flask import render_template
from flask import request
app = Flask(__name__)

@app.route('/')
def start():
    return render_template('route_map.html')

@app.route('/navigate', methods=['POST'])
def gotcoords():
    print(request.form) #Received POST data in request.form
