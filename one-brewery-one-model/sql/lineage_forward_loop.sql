CREATE TABLE #path (node VARCHAR(40), share FLOAT, depth INT);
INSERT INTO #path
  SELECT to_node, share, 1 FROM edge WHERE from_node = 'M-26-0087';
DECLARE @d INT = 1;
WHILE @d < 12
BEGIN
  INSERT INTO #path
    SELECT e.to_node, p.share * e.share, @d + 1
    FROM #path p JOIN edge e ON e.from_node = p.node
    WHERE p.depth = @d;
  IF @@ROWCOUNT = 0 BREAK;
  SET @d = @d + 1;
END;
SELECT node, SUM(share) AS share FROM #path GROUP BY node;
