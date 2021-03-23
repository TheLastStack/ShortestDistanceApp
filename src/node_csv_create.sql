/* Adds id to nodes, takes distinct node. Also transforms node from EPSG:3857 to EPSG:4326*/
DROP TABLE IF EXISTS graph_node;
CREATE TABLE graph_node AS
SELECT
	node, ST_X(node_4326) lon, ST_Y(node_4326) lat, ROW_NUMBER() OVER ( ORDER BY node) AS id
FROM
	(SELECT
		DISTINCT node node
	 FROM
		spliced_edges
	 GROUP BY
		node
	) sq1,
	LATERAL
		ST_Transform(node, 4326) node_4326;
COPY (SELECT id, lon, lat FROM graph_node) TO 'D:\nodes.csv' DELIMITER ',' CSV HEADER;
