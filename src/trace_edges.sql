/* Connecting all node pairs to each other*/
DROP TABLE IF EXISTS intersection_edges;
CREATE TABLE intersection_edges AS
WITH t AS (
SELECT
	a.node as start_node, b.node as end_node, a.frac as start_frac, b.frac as end_frac, a.edge AS start_edge, b.edge AS end_edge, a.oneway AS start_oneway, b.oneway AS end_oneway
FROM
	intersection_points_new a,
	intersection_points_new b
WHERE
	a.r_id + 1 = b.r_id
),
t_strict AS (
	SELECT
		start_node, end_node, start_oneway, end_oneway, ST_LineSubstring(start_edge, start_frac, end_frac) as final_edge
	FROM
		t
	WHERE
		start_edge = end_edge
		AND start_frac < end_frac
)
SELECT
	node, edge, oneway, ROW_NUMBER () OVER (
						ORDER BY node, edge
	) AS r_id
FROM
	(SELECT
		start_node AS node, final_edge AS edge, start_oneway oneway
	 FROM
		t_strict
	 UNION
	 SELECT
		end_node AS node, final_edge AS edge, end_oneway oneway
	 FROM
		t_strict
	 UNION
	 SELECT
		start_node as node, ST_LineSubString(start_edge, start_frac, 1), start_oneway oneway
	 FROM
		t
	 WHERE
		start_frac < 1 AND end_frac = 0
	) d;
COPY (SELECT source, target, wkt FROM graph_edges) TO 'D:\edges.csv' DELIMITER ',' CSV HEADER;
