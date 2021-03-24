from urllib import parse
from urllib import request as req
import os
import sys
import subprocess
import argparse
import psycopg2 as psy


def create_database(PREFIX_STRING, XML_NAME, DB_PASSWORD, DB_NAME, DB_USER):
    print("Accessing " + PREFIX_STRING)
    if os.name.lower() in ['windows', 'nt']:
        if subprocess.call("powershell -Command \"$env:PGPASSWORD='{}'; psql -U {} -c 'create database {} encoding utf8;'\"".format(DB_PASSWORD, DB_USER, DB_NAME)) != 0:
            sys.exit(1)
        if subprocess.call("powershell -Command \"$env:PGPASSWORD='{}'; psql -U {} -d {} -c 'create extension postgis;'\"".format(DB_PASSWORD, DB_USER, DB_NAME)) != 0:
            sys.exit(1)
        if subprocess.call("powershell -Command \"$env:PGPASSWORD='{}'; psql -U {} -d {} -c 'create extension hstore;'\"".format(DB_PASSWORD, DB_USER, DB_NAME)) != 0:
            sys.exit(1)
    else:
        if subprocess.run(['psql', PREFIX_STRING, '-U', DB_USER, '-c', '\'create database {} encoding utf8;\''.format(DB_NAME)], capture_output=True).stderr is not None:
            sys.exit(1)
        if subprocess.run(['psql', PREFIX_STRING, '-U', DB_USER, '-d', DB_NAME, '-c', '\'create extension postgis;\''], capture_output=True).stderr is not None:
            sys.exit(1)
        if subprocess.run(['psql', PREFIX_STRING, '-U', DB_USER, '-d', DB_NAME, '-c', '\'create extension hstore;\''], capture_output=True).stderr is not None:
            sys.exit(1)

def modify_database(DB_NAME, DB_PASSWORD, DB_USER, DB_HOST, DB_PORT, XML_NAME):
    if input("Is osm2pgsql added to path? (Y/N)").lower() == "n":
        try:
            path = input('Enter path to osm2pgsql binary>')
            output = subprocess.run(
                [os.path.join(os.path.join(os.getcwd(), path), 'osm2pgsql.exe'),
                 '-S', os.path.join(os.path.join(os.getcwd(), path), 'default.style'),
                 '-W', '-U', DB_USER, '-d', DB_NAME, '-H', DB_HOST, '-P',
                 DB_PORT, XML_NAME, '--hstore'],
                shell=True, check=True)
        except subprocess.CalledProcessError as exc:
            print("Status : FAIL", exc.returncode, exc.output)
            sys.exit(1)
    else:
        try:
            output = subprocess.run(
                ['osm2pgsql',
                 '-s', '-W', '-U', DB_USER, '-d', DB_NAME, '-H', DB_HOST, '-P', DB_PORT, XML_NAME, '--hstore'],
                shell=True, check=True)
        except subprocess.CalledProcessError as exc:
            print("Status : FAIL", exc.returncode, exc.output)
            sys.exit(1)
    if input("Do you want to preprocess data before use now (Y/N)? Note: Preprocessing can take up to 8 hrs.").lower() == "y":
        with psy.connect(database=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT) as conn:
            with conn.cursor() as cur:
                print("Finding motorable roads ...")
                with open("trace_roads.sql", "r", encoding="utf-8") as sql_build:
                    cur.execute(sql_build.read())
            with conn.cursor() as cur:
                print("Finding road intersections ...")
                with open("find_intersections.sql", "r", encoding="utf-8") as sql_build:
                    cur.execute(sql_build.read())
            with conn.cursor() as cur:
                print("Breaking roads to edges between nodes ...")
                with open("trace_edges.sql", "r", encoding="utf-8") as sql_build:
                    cur.execute(sql_build.read())
            with conn.cursor() as cur:
                print("Removing unnecessay nodes and splicing edges ...")
                with open("splice_edges.sql", "r", encoding="utf-8") as sql_build:
                    cur.execute(sql_build.read())
            with conn.cursor() as cur:
                print("Building a list of valid nodes in EPSG 4326...")
                with open("node_csv_create.sql", "r", encoding="utf-8") as sql_build:
                    cur.execute(sql_build.read())
            with conn.cursor() as cur:
                print("Building a list of valid edges in EPSG 4326...")
                with open("edge_csv_create.sql", "r", encoding="utf-8") as sql_build:
                    cur.execute(sql_build.read())
            with conn.cursor() as cur:
                print("Exporting lists as csv...")
                cur.execute("COPY (SELECT id, lon, lat FROM graph_node) TO '%s' DELIMITER ',' CSV HEADER;",
                            (os.path.join(os.getcwd(), "WebServer", "Nodes", "nodes.csv"),))
                cur.execute("COPY (SELECT source, target, length, wkt FROM graph_edges) TO '%s' DELIMITER ',' CSV HEADER;",
                            (os.path.join(os.getcwd(), "WebServer", "Nodes", "edges.csv"),))
        print("Preprocessing complete")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This script initializes the postGIS database.'
        'Ensure you have installed PostgreSQL and PostGIS extension before starting the installation'
        'Please ensure you have either installed osm2pgsql or provide a path to an installed copy.')
    parser.add_argument('-U','--DBUSER', default='postgres', help="User Name of PostGIS database")
    parser.add_argument('-d', '--DBNAME', default='osm', help="Name of PostGIS database to create/overwrite")
    parser.add_argument('-W', '--DBPASSWORD', help="Password for user authentication")
    parser.add_argument('-H', '--DBHOST', default='localhost', help="Network address of database server")
    parser.add_argument('-P', '--DBPORT', default="5432", help="Port for the server")
    parser.add_argument('-X', '--XML', help="OSM XML file to use")
    parser.add_argument('-L', nargs=4, help="Co-ordinates to restrict query to. Write in format ymin xmin ymax xmax")
    args = parser.parse_args();
    DB_USER = args.DBUSER
    DB_NAME = args.DBNAME
    DB_PASSWORD = args.DBPASSWORD
    DB_HOST = args.DBHOST
    DB_PORT = args.DBPORT
    XML_NAME = args.XML
    PREFIX_STRING = "postgresql://{}:{}@{}:{}".format(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
    if args.L is not None:
        COORDS = [float(i) for i in args.L]
    else:
        COORDS = None
    if XML_NAME is None:
        if COORDS is None:
            sys.exit(1)
        custom_min = lambda x : (round(min(x) * 50) - 1) / 50
        custom_max = lambda x : (round(max(x) * 50) + 1) / 50
        min_y = custom_min((COORDS[0],))
        min_x = custom_min((COORDS[1],))
        max_y = custom_max((COORDS[2],))
        max_x = custom_max((COORDS[3],))
        request_string = "(way({s},{w},{n},{e});node({s},{w},{n},{e});rel({s},{w},{n},{e}););out body;"
        req.urlretrieve('https://overpass-api.de/api/interpreter?data=' +
                            parse.quote_plus(request_string.format(s=min_y, w=min_x, n=max_y, e=max_x),
                                            safe="[]();.,"),
                         os.path.join(os.getcwd(), "osm_d.osm"))
        XML_NAME = 'osm_d.osm'
    if input("Do you want to create a database (Y/N)?").lower() == "y":
        create_database(XML_NAME=XML_NAME, DB_NAME=DB_NAME, PREFIX_STRING=PREFIX_STRING, DB_USER=DB_USER, DB_PASSWORD=DB_PASSWORD, COORDS=COORDS)
    if input("Do you want to transfer data into the named database(Y/N)? ").lower() == "y":
        modify_database(DB_NAME=DB_NAME, DB_USER=DB_USER, DB_HOST=DB_HOST, DB_PORT=DB_PORT, XML_NAME=XML_NAME, DB_PASSWORD=DB_PASSWORD)
    with open("credentials.key", "w") as location:
        location.write(PREFIX_STRING + "\n")
        location.write(DB_NAME)
