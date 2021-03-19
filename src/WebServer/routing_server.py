from flask import Flask
from flask import render_template
from flask import request
import os
import dicttoxml
import random

app = Flask(__name__)


class Edge:
    '''
    Edge defines an edge in a graph.
    edge_length (float value) gives the length of the edge in the graph.
    directed (boolean value) specifies whether the edge is directed. Is true if directed
    _completed is an internal variable used to check whether the edge has been explored
    '''
    def __init__(self, edge_length, directed, tail=None, head=None):
        '''Initializes the edge'''
        self.edge_length = edge_length
        self.directed = directed
        self.tail = tail
        self.head = head
        self._completed = False
    def __len__(self):
        '''len(Edge) gives the edge distance'''
        return self.edge_length
    def isDone(self):
        '''Has the edge been explored completely?'''
        return self._completed
    def done(self):
        '''Used to signify that nodes beyond this edge have been exhausted'''
        self._completed = True
    def __set__(self, instance, edge_length):
        raise AttributeError("Attempting to change edge length")
    def __set__(self, instance, directed):
        raise AttributeError("Attempting to change directionality of edge")
    def __set__(self, instance, _completed):
        raise AttributeError("Attempting to change edge status")


class EdgeIterator:
    '''Defines an iterator. Allows use of edges in all places an iterator may be used'''
    def __init__(self, caller_instance):
        self._idx = 0
        self._caller_instance = caller_instance
    def __next__(self):
        self._idx += 1
        if self._idx < len(self._caller_instance.edges):
            return self._caller_instance.edges[self._idx]
        else:
            raise StopIteration("Exhausted edges")

class Node:
    '''
    Node defines a node in a graph.
    x (float) and y (float) define the position of the node
    edges stores edges associated with a node.
    '''
    def __init__(self, x, y, edges):
        '''
        Pass in x, y values and an iterator returning edges
        In case of directed edges, push it into the tail node only and set
        edge head to point to the required node.
        a -> b
        Push edge into a only
        '''
        self.x = x
        self.y = y
        self.edges = []
        for edge in edges:
            if edge.directed:
                if edge.tail is None:
                    edge.tail = self
                else:
                    raise ValueError("Attempting to push a directed edge to another node")
            else:
                if edge.head is None:
                    edge.head = self
                elif edge.tail is None:
                    edge.tail = self
                else:
                    raise ValueError("Attempting to push an edge into more than two nodes")
            if edge.directed:
                if edge.head is self:
                    raise ValueError("Attempting to push directed edge into head")
            self.edges.append(edge)
    def __iter__(self):
        '''
        Use this to iterate over all edges. Allows use in for loop
        '''
        return EdgeIterator(self)
    def isDone(self):
        '''
        Check whether all edges attached to the node have been exhausted
        '''
        for edge in self.edges:
            if not edge.isDone():
                return False
        return True
    def __getitem__(self, idx):
        '''
        Allows access to edges with index operators. Use a[0] to access edge at a.edges[0] of
        node a.
        '''
        return self.edges[idx]
    def __setitem__(self, idx, value):
        return self.edges[idx] = value


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
