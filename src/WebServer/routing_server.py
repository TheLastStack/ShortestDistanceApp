from flask import Flask
from flask import render_template
from flask import request
from statistics import mean
import pandas as pd
import heapq
import networkx as nx
import os
import dicttoxml
import random

app = Flask(__name__)

latlonData = pd.read_csv(os.path.join(os.getcwd(), os.path.join("Nodes", "nodes.csv")))
graphData = pd.read_csv(os.path.join(os.getcwd(), os.path.join("Nodes", "edges.csv")))
graphData = graphData[["source", "target", "length"]]
graphType = nx.Graph()
g = nx.from_pandas_edgelist(graphData, edge_attr="length", create_using=graphType)

def calculateHeuristic(currNode):
    [currLat, currLon] = latlonData[latlonData["id"] == currNode].iloc[0][["lat", "lon"]]
    curr = (currLat, currLon)
    dest = (17.240673, 78.432342)
    #return haversine(curr, dest)
    return (abs(curr[0]-dest[0]) + abs(curr[1]-dest[1]))
    '''
    Both returns can be used: manhattan distance formula or haversine,
    both will give same answer
    calculating manhattan distnace is faster than haversine distance.

    Aprox 50% less time was taken
    '''

def createPath(last_node, current):
    path = [current]
    while current in last_node.keys():
        current = last_node[current]
        path.insert(0, current)
    return path

def aStar(srcNode, destNode):
    open_list = []

    last_node = {}
    last_node[srcNode] = None

    cost = {}
    cost[srcNode] = 0

    heuristic_value = {}
    heuristic_value[srcNode] = 0

    gScore = {}
    gScore[srcNode] = 0

    heapq.heappush(open_list, (srcNode, heuristic_value))

    while len(open_list) > 0:
        currentNode = heapq.heappop(open_list)

        if currentNode[0] == destNode:
            return createPath(last_node, currentNode[0])

        neighbourData = list(g.neighbors(currentNode[0]))

        for item in neighbourData:
            neighbourNode = item
            distance = g[currentNode[0]][neighbourNode]["length"]

            if neighbourNode not in last_node:
                cost[neighbourNode] = gScore[currentNode[0]] + distance

                if cost[neighbourNode] < gScore.get(neighbourNode, float("inf")):
                    last_node[neighbourNode] = currentNode[0]
                    gScore[neighbourNode] = cost[neighbourNode]
                    heuristic_value[neighbourNode] = gScore[neighbourNode] + calculateHeuristic(neighbourNode)

                    if neighbourNode not in open_list:
                        heapq.heappush(open_list, (neighbourNode, heuristic_value))

    return open_list


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
    srcNode = 7065632060
    destNode = 5711258337
    route = aStar(srcNode, destNode)
    route.pop(0)
    if len(route) == 0:
        print("Path Not Found")
    resulting_nodes = []
    for node in route:
        [lat, lon] = latlonData[latlonData["id"] == node].iloc[0][["lat", "lon"]]
        resulting_nodes.append((lon, lat))
    # Path from A* will be of form: [(x0, y0), (x1, y1), ...]
    # Below statement is a placeholder
    xml_request_dict = {u'result':[]}
    for x, y in resulting_nodes:
        xml_request_dict[u'result'] += [{u'x': x, u'y': y}]
    # Result being sent back.
    print(dicttoxml.dicttoxml(xml_request_dict, item_func=lambda x: u'node', root=False, attr_type=False))
    return dicttoxml.dicttoxml(xml_request_dict, item_func=lambda x: u'node', root=False, attr_type=False)
