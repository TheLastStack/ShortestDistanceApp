from urllib import parse
from urllib import request as req
import os
import sys
import subprocess
import argparse


def create_database(PREFIX_STRING, XML_NAME, DB_PASSWORD, DB_NAME, DB_USER, COORDS=None):
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

def modify_database(DB_NAME, DB_USER, DB_HOST, DB_PORT, XML_NAME):
    if os.name.lower() in ['windows', 'nt']:
        try:
            path = input('Enter path to osm2pgsql binary>')
            output = subprocess.run(
                [path + '\\osm2pgsql',
                 '-S', '{}\\default.style'.format(path), '-W', '-U', DB_USER, '-d', DB_NAME, '-H', DB_HOST, '-P', DB_PORT, XML_NAME, '--hstore'],
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
    if input("Do you want to create a database (Y/N)?").lower() == "y":
        create_database(XML_NAME=XML_NAME, DB_NAME=DB_NAME, PREFIX_STRING=PREFIX_STRING, DB_USER=DB_USER, DB_PASSWORD=DB_PASSWORD, COORDS=COORDS)
    if input("Do you want to transfer data into the named database(Y/N)? ").lower() == "y":
        modify_database(DB_NAME=DB_NAME, DB_USER=DB_USER, DB_HOST=DB_HOST, DB_PORT=DB_PORT, XML_NAME=XML_NAME)
    with open("credentials.key", "w") as location:
        location.write(PREFIX_STRING + "\n")
        location.write(DB_NAME)
