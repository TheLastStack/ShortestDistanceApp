/* Creating functions for finding start and end of ST_MultiLineString */
create or replace function ST_multiline_start(multi_line geometry)
returns geometry
language plpgsql
as
$$
declare
   return_string geometry;
begin
	SELECT
		ST_StartPoint(a_line[array_upper(a_line, 1)])
	INTO
		return_string
	FROM
		(SELECT
			array_agg((lines).geom) AS a_line
		FROM
			(SELECT multi_line afd) asd,
		LATERAL
			ST_Dump(asd.afd)  AS lines(line)
			) demp;

   return return_string;
end;
$$;
create or replace function ST_multiline_end(multi_line geometry)
returns geometry
language plpgsql
as
$$
declare
   return_string geometry;
begin
	SELECT
		ST_EndPoint(a_line[1])
	INTO
		return_string
	FROM
		(SELECT
			array_agg((lines).geom) AS a_line
		 FROM
				(SELECT multi_line afd) asd,
				LATERAL
					ST_Dump(asd.afd)  AS lines(line)
			) demp;

   return return_string;
end;
$$;
/* Rewrites edges between nodes in term of their ids. Takes into account oneway roads while calculating*/
DROP TABLE IF EXISTS graph_edges;
CREATE TABLE graph_edges AS
SELECT
	wkt, source, graph_node.id target, edge
FROM
	(SELECT
		ST_AsText(ST_Transform(edge, 4326)) wkt, graph_node.id source, COALESCE(ST_EndPoint(edge), ST_multiline_end(edge)) end_node, edge
	FROM
		(SELECT
			node, edge, oneway
		 FROM
			spliced_edges
		 WHERE
			ST_Equals(COALESCE(ST_StartPoint(edge), ST_multiline_start(edge)), node)
			AND oneway ILIKE 'yes'
		 )spl_edge
	LEFT JOIN graph_node ON graph_node.node = spl_edge.node) start_nodes
	LEFT JOIN graph_node ON graph_node.node = end_node
UNION
SELECT
	wkt, source, graph_node.id target, edge
FROM
	(SELECT
		ST_AsText(ST_Transform(edge, 4326)) wkt, graph_node.id source, COALESCE(ST_StartPoint(edge), ST_multiline_start(edge)) start_node, edge
	FROM
		(SELECT
			node, edge, oneway
		 FROM
			spliced_edges
		 WHERE
			ST_Equals(COALESCE(ST_EndPoint(edge), ST_multiline_end(edge)), node)
			AND oneway ILIKE '-1'
		 )spl_edge
	LEFT JOIN graph_node ON graph_node.node = spl_edge.node) end_nodes
	LEFT JOIN graph_node ON graph_node.node = start_node
UNION
SELECT
	wkt, source, graph_node.id target, edge
FROM
	(SELECT
		ST_AsText(ST_Transform(edge, 4326)) wkt, graph_node.id source, edge,
	 	CASE
	 		WHEN COALESCE(ST_StartPoint(edge), ST_multiline_start(edge)) = graph_node.node
	 		THEN COALESCE(ST_EndPoint(edge), ST_multiline_end(edge))
	 		ELSE COALESCE(ST_StartPoint(edge), ST_multiline_start(edge))
	 	END start_node
	FROM
		(SELECT
			node, edge, oneway
		 FROM
			spliced_edges
		 WHERE
			oneway IS NULL OR NOT oneway ILIKE ANY(ARRAY['-1', 'yes'])
		 )spl_edge
	LEFT JOIN graph_node ON graph_node.node = spl_edge.node) end_nodes
	LEFT JOIN graph_node ON graph_node.node = start_node;
