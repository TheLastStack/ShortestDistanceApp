from flask import Flask
from flask import render_template
from flask import request
from statistics import mean
from shapely import wkt
from shapely import ops as shops
import pandas as pd
import heapq
import networkx as nx
import os
import sys
import dicttoxml
import time

app = Flask(__name__)

latlonData = pd.read_csv(os.path.join(os.getcwd(), "Nodes", "Speed_nodes.csv"))
graphData = pd.read_csv(os.path.join(os.getcwd(), os.path.join("Nodes", "speed_edges.csv")))
graphData = graphData[["source", "target", "length", "maxspeed", "wkt"]]
graphData["time"] = graphData["length"] / graphData["maxspeed"]
graphType = nx.DiGraph()
g = nx.from_pandas_edgelist(graphData, edge_attr=["time", "wkt", "length"], create_using=graphType)

def calculateHeuristic(currNode, dest):
    try:
        [currLat, currLon] = latlonData[latlonData["id"] == currNode].iloc[0][["lat", "lon"]]
    except:
        print(currNode)
        sys.exit(1)
    curr = (currLat, currLon)
    return (abs(curr[0]-dest[0]) + abs(curr[1]-dest[1]))
    '''
    Both returns can be used: manhattan distance formula or haversine,
    both will give same answer
    calculating manhattan distnace is faster than haversine distance.

    Aprox 50% less time was taken
    '''

def createPath(last_node, current):
    path = [current]
    ETA = 0
    distance = 0
    while current in last_node.keys():
        current = last_node[current]
        if current is not None:
            ETA += float(current[2])
            distance += float(current[3])
            path.insert(0, (current[0], current[1]))
            current = current[0]
    return path, ETA, distance

def aStar(srcNode, destNode, dest, x, y):
    open_list = []

    last_node = {}
    last_node[srcNode] = None

    cost = {}
    cost[srcNode] = 0

    heuristic_value = 0

    gScore = {}
    gScore[srcNode] = 0

    heapq.heappush(open_list, (heuristic_value, srcNode))

    while len(open_list) > 0:
        currentNode = heapq.heappop(open_list)

        if currentNode[1] == destNode:
            return createPath(last_node, currentNode[1])

        neighbourData = list(g.neighbors(currentNode[1]))

        for item in neighbourData:
            neighbourNode = item
            time = pow(g[currentNode[1]][neighbourNode]["length"],x)*pow(g[currentNode[1]][neighbourNode]["time"],y)

            if neighbourNode not in last_node:
                cost[neighbourNode] = gScore[currentNode[1]] + time

                if cost[neighbourNode] < gScore.get(neighbourNode, float("inf")):
                    last_node[neighbourNode] = (currentNode[1], g[currentNode[1]][neighbourNode]["wkt"],
                        g[currentNode[1]][neighbourNode]["time"], g[currentNode[1]][neighbourNode]["length"])

                    gScore[neighbourNode] = cost[neighbourNode]
                    heuristic_value = gScore[neighbourNode] + calculateHeuristic(neighbourNode, dest)

                    if neighbourNode not in open_list:
                        heapq.heappush(open_list, (heuristic_value, neighbourNode))

    return open_list, 0.0, 0.0


@app.route('/')
def start():
    return render_template('route_map.html')

@app.route('/navigate', methods=['POST'])
def gotcoords():
    entered_points = {}
    for key, value in request.form.lists():
        entered_points[key] = float(value[0])
    # Received Points are present in dictionary here.
    # A* algorithm here
    #7065632060
    #5711258337
    srcNode = latlonData.iloc[
                ((latlonData["lat"] - entered_points['white_y']).abs() + (latlonData["lon"] - entered_points['white_x']).abs()).idxmin()
                ]["id"]
    destNode = latlonData.iloc[
                ((latlonData["lat"] - entered_points['black_y']).abs() + (latlonData["lon"] - entered_points['black_x']).abs()).idxmin()
                ]
    dest = (destNode["lon"], destNode["lat"])
    destNode = destNode["id"]
    print(srcNode)
    print(destNode)
    print(entered_points)
    start = time.time()
    if entered_points["least"] == 0:
        route, Time_taken, Total_Distance = aStar(srcNode, destNode, dest, 1, 0)
    else:
        route, Time_taken, Total_Distance = aStar(srcNode, destNode, dest, 0, 1)
    print(Time_taken)
    print(Total_Distance)
    print(time.time() - start)
    try:
        route.pop(0)
    except IndexError:
        pass
    # Path from A* will be of form: [(x0, y0), (x1, y1), ...]
    xml_request_dict = {u'result':[]}
    if len(route) > 0:
        resulting_nodes = []
        for i in route[:-1]:
            [lat, lon] = latlonData[latlonData["id"] == i[0]].iloc[0][["lat", "lon"]]
            try:
                pulled_edge = list((wkt.loads(i[1])).coords)
            except NotImplementedError:
                pulled_edge = list((shops.linemerge(list((wkt.loads(i[1])).geoms))).coords)
            if pulled_edge[-1] == (lon, lat):
                pulled_edge = reversed(pulled_edge)
            for x, y in pulled_edge:
                resulting_nodes.append((x, y))
        edge = graphData[(graphData["source"] == route[-1]) & (graphData["target"] == route[-2][0])]
        if (edge.empty):
            edge = graphData[(graphData["source"] == route[-2][0]) & (graphData["target"] == route[-1])].iloc[0]["wkt"]
            [lat, lon] = latlonData[latlonData["id"] == route[-2][0]].iloc[0][["lat", "lon"]]
        else:
            edge = edge.iloc[0]["wkt"]
            [lat, lon] = latlonData[latlonData["id"] == route[-1]].iloc[0][["lat", "lon"]]
        try:
            pulled_edge = list((wkt.loads(i[1])).coords)
        except NotImplementedError:
            pulled_edge = list((shops.linemerge(list((wkt.loads(i[1])).geoms))).coords)
        if pulled_edge[-1] == (lon, lat):
            pulled_edge = reversed(pulled_edge)
        for x, y in pulled_edge:
            resulting_nodes.append((x, y))
        for x, y in resulting_nodes:
            xml_request_dict[u'result'] += [{u'x': x, u'y': y}]
        xml_request_dict[u'length'] = Total_Distance / 1000
        xml_request_dict[u'time'] = Time_taken / 1000
    else:
        xml_request_dict[u'result'] = 'None'
    # Result being sent back.
    return dicttoxml.dicttoxml(xml_request_dict, item_func=lambda x: u'node', root=True, attr_type=False)
