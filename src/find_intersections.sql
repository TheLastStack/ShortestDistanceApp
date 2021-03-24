/* Finding intersection of all line pairs */
DROP TABLE IF EXISTS intersection_points_new;
CREATE TABLE
	intersection_points_new AS
WITH intersector AS (
SELECT
	(ST_Dump(ST_Intersection(a.way, b.way))).geom AS node, a.way AS edge, a.oneway AS oneway, a.highway AS highway, a.tags -> 'maxspeed' AS maxspeed,
	a.bridge AS a_bridge, b.bridge AS b_bridge, a.tunnel AS a_tunnel, b.tunnel AS b_tunnel, a.z_order AS a_res,
	b.z_order AS b_res
FROM
	motor_roads a
INNER JOIN motor_roads b ON ST_Touches(a.way, b.way) AND a.osm_id <> b.osm_id
)
SELECT
	node, edge, frac, highway, oneway, maxspeed, ROW_NUMBER () OVER (
						ORDER BY edge, frac
	) AS r_id
FROM
	(SELECT
		node, edge, ST_LineLocatePoint(edge, node) AS frac, oneway, highway, maxspeed
	 FROM
		(SELECT
		 	node, edge, oneway, highway, maxspeed
		 FROM
		 	intersector
		 WHERE
		 	a_bridge IS NULL AND b_bridge IS NULL
		 	AND a_tunnel IS NULL AND b_tunnel IS NULL
		 UNION
		 SELECT
			node, edge, oneway, highway, maxspeed
		 FROM
			intersector
		 WHERE
			a_bridge = b_bridge AND
		 	a_res = b_res
		 UNION
		 SELECT
			node, edge, oneway, highway, maxspeed
		 FROM
			intersector
		 WHERE
			a_tunnel = b_tunnel AND
		 	a_res = b_res
	 	) AS derived_table
	 UNION
	 SELECT
		ST_StartPoint(a.way) AS node, a.way AS edge, ST_LineLocatePoint(a.way,ST_StartPoint(a.way)) AS frac, a.oneway AS oneway, a.highway AS highway, a.tags -> 'maxspeed' AS maxspeed
	 FROM
		motor_roads a
	 UNION
	 SELECT
		ST_EndPoint(a.way) AS node, a.way as edge, ST_LineLocatePoint(a.way,ST_EndPoint(a.way)) AS frac, a.oneway as oneway, a.highway AS highway, a.tags -> 'maxspeed' AS maxspeed
	 FROM
		motor_roads a
	) AS derived_table2;
