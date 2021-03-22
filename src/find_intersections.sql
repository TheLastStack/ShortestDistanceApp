/* Finding intersection of all line pairs */
DROP TABLE IF EXISTS intersection_points_new;
CREATE TABLE
	intersection_points_new AS
SELECT
	node, edge, frac, oneway, ROW_NUMBER () OVER (
						ORDER BY edge, frac
	) AS r_id
FROM
	(SELECT
		node, edge, ST_LineLocatePoint(edge, node) AS frac, oneway
	 FROM
		(SELECT
			(ST_Dump(ST_Intersection(a.way, b.way))).geom AS node, a.way AS edge, a.oneway AS oneway
		 FROM
			motor_roads as a,
			motor_roads as b
		 WHERE
			ST_Touches(a.way, b.way)
			AND a.osm_id != b.osm_id
			AND ((a.bridge IS NULL AND b.bridge IS NULL) OR (a.bridge IS NOT NULL AND b.bridge IS NOT NULL))
			AND (a.bridge IS NULL OR a.z_order = b.z_order)) AS derived_table
	 UNION
	 SELECT
		ST_StartPoint(a.way) AS node, a.way AS edge, ST_LineLocatePoint(a.way,ST_StartPoint(a.way)) AS frac, a.oneway as oneway
	 FROM
		motor_roads a
	 UNION
	 SELECT
		ST_EndPoint(a.way) AS node, a.way as edge, ST_LineLocatePoint(a.way,ST_EndPoint(a.way)) AS frac, a.oneway as oneway
	 FROM
		motor_roads a
	) AS derived_table2;
