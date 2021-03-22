/* This SQL query traces all roads in the map*/
DROP TABLE IF EXISTS motor_roads;
CREATE TABLE motor_roads AS
	SELECT
	 	*
	FROM
		planet_osm_line
	WHERE
		highway ILIKE ANY (ARRAY['motorway', 'trunk', 'primary', 'secondary', 'tertiary',
								 'unclassified', 'residential', 'motorway_link', 'trunk_link',
								 'primary_link', 'secondary_link', 'tertiary_link', 'living_street',
								 'service', 'pedestrian', 'track', 'raceway', 'road', 'path']);
--These highway tags indicate a road capable of some degreee of vehicular movement
