-- Backward trace: the forward query with from_node and to_node swapped in the four places they appear.
-- The start node is the first can pallet of pack lot L260412-C1-1 (its SSCC).
WITH RECURSIVE backward AS (
  SELECT from_node AS node, share, 1 AS depth
  FROM edge
  WHERE to_node = '006141412600000416'
  UNION ALL
  SELECT e.from_node, f.share * e.share, f.depth + 1
  FROM backward f
  JOIN edge e ON e.to_node = f.node
  WHERE f.depth < 12
)
SELECT node, SUM(share) AS share
FROM backward
GROUP BY node;
