from flask import Flask
from flask import render_template
from flask import request
import os
import dicttoxml
import random

app = Flask(__name__)

@app.route('/')
def start():
    return render_template('route_map.html')

@app.route('/navigate', methods=['POST'])
def gotcoords():
    print(request.form) #Received POST data in request.form
    entered_points = {}
    for key, value in request.form.lists():
        entered_points[key] = value[0]
    print(entered_points)
    # Received Points are present in dictionary here.
    # A* algorithm here
    # Path from A* will be of form: [(x0, y0), (x1, y1), ...]
    # Below statement is a placeholder
    resulting_nodes = [(0, 0), (random.randint(0, 40), random.randint(0, 40))]
    xml_request_dict = {u'result':[]}
    for x, y in resulting_nodes:
        xml_request_dict[u'result'] += [{u'x': x, u'y': y}]
    # Result being sent back.
    print(dicttoxml.dicttoxml(xml_request_dict, item_func=lambda x: u'node', root=False, attr_type=False))
    return dicttoxml.dicttoxml(xml_request_dict, item_func=lambda x: u'node', root=False, attr_type=False)


with open(os.path.join(os.path.dirname(os.getcwd()), "credentials.key"), "r") as location:
    file = location.read().splitlines()
PREFIX_STRING = file[0] #Prefix string contains all required database server details
DB_NAME = file[1]
