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
/* Prunes nodes present on lines and then splices together the resulting nodes*/
DROP TABLE IF EXISTS spliced_edges;
CREATE TABLE spliced_edges AS
WITH dt AS
	(SELECT
			b.edge AS edge1, d.edge AS edge2, ST_LineMerge(ST_Union(b.edge, d.edge)) AS spliced_edge, b.node AS deleted_node
	FROM
		(SELECT
			node AS node, COUNT(node) AS num
		FROM
			(SELECT
				node, edge
			FROM
				intersection_edges
			UNION
			SELECT
				COALESCE(ST_StartPoint(edge), ST_multiline_start(edge)), edge
			FROM
				intersection_edges
			UNION
			SELECT
				COALESCE(ST_EndPoint(edge), ST_multiline_end(edge)), edge
			FROM
				intersection_edges
			) all_nodes
		GROUP BY
			node
		) e,
		intersection_edges b,
		intersection_edges d
	WHERE
		e.num = 2 AND
		e.node = b.node AND
		e.node = d.node AND
		((b.oneway IS NOT NULL AND d.oneway IS NOT NULL AND b.oneway = d.oneway) OR
		(b.oneway IS NULL AND d.oneway IS NULL)) AND
		b.r_id <> d.r_id AND
		(NOT (ST_IsClosed(b.edge) OR ST_IsClosed(d.edge)))
	),
dtt AS (
	SELECT
		DISTINCT ON(a.spliced_edge) a.spliced_edge AS idx_spliced_edge, ST_LineMerge(ST_Union(a.spliced_edge, b.spliced_edge)) final_edge, ST_Length(a.spliced_edge) as slength
	FROM
		dt a,
		dt b
	WHERE
		ST_Overlaps(a.spliced_edge, b.spliced_edge) AND
		NOT ST_Equals(a.spliced_edge, b.spliced_edge)
	ORDER BY
		a.spliced_edge,
		slength DESC),
merged_lines AS
	(SELECT
		deleted_node, edge1, edge2,
		CASE
			WHEN idx_spliced_edge IS NULL
			THEN asd.spliced_edge
			ELSE final_edge
		END AS final_spliced_edge
	FROM
		(SELECT
			*
		FROM
			dtt
		RIGHT JOIN dt ON dt.spliced_edge = dtt.idx_spliced_edge) asd
	 ),
filtered AS
(SELECT
	node, edge, deleted_node, oneway
 FROM
	(SELECT
		node, deleted_node, oneway,
		CASE
			WHEN edge1 = edge
			THEN final_spliced_edge
			WHEN edge2 = edge
			THEN final_spliced_edge
			ELSE edge
		END AS edge
	FROM
		(SELECT
			*
		FROM
			merged_lines
		RIGHT JOIN
			intersection_edges
		ON
			edge1 = edge OR edge2 = edge) combining
	 ) togroup
	GROUP BY
		node,
		edge,
		oneway,
		deleted_node
),
adding_spliced_edges AS
(
	SELECT
		edge, COALESCE(ST_StartPoint(edge), ST_multiline_start(edge)) AS node_1, COALESCE(ST_EndPoint(edge), ST_multiline_end(edge)) AS node_2, oneway
	FROM
		filtered
	WHERE
		deleted_node IS NOT NULL
)
SELECT
	node, edge, oneway
FROM
	filtered
WHERE
	deleted_node IS NULL
UNION
SELECT
	fd.node, asd.edge, asd.oneway
FROM
	adding_spliced_edges asd,
	filtered fd
WHERE
	asd.node_1 = fd.node OR asd.node_2 = fd.node;
