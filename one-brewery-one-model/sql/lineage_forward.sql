WITH RECURSIVE forward AS (
  SELECT to_node AS node, share, 1 AS depth
  FROM edge
  WHERE from_node = 'M-26-0087'
  UNION ALL
  SELECT e.to_node, f.share * e.share, f.depth + 1
  FROM forward f
  JOIN edge e ON e.from_node = f.node
  WHERE f.depth < 12
)
SELECT node, SUM(share) AS share
FROM forward
GROUP BY node;
