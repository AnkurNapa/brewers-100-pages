-- The node and edge views of Appendix C.3, in SQLite. They run unchanged on PostgreSQL.
-- A node is anything with an ID that material passes through. Surrogate keys repeat across
-- tables, so a movement names the node type beside the key.
CREATE VIEW IF NOT EXISTS node AS
SELECT CASE WHEN lot_type = 'pack' THEN 'pack_lot' ELSE 'lot' END AS node_type,
       lot_key AS node_key, lot_id AS node_id
FROM lot
UNION ALL SELECT 'brew', brew_key, brew_id FROM brew
UNION ALL SELECT 'batch', batch_key, batch_id FROM batch
UNION ALL SELECT 'pallet', package_unit_key, sscc FROM package_unit;

-- One movement with its share: the quantity on the edge over the sum of that material class
-- arriving at the same node (chapter 9.2). Wort, beer and packed beer are one class: liquid.
-- Shipments to customers are movements but not edges, because a customer is not a node.
CREATE VIEW IF NOT EXISTS edge AS
WITH m AS (
  SELECT fn.node_id AS from_node, tn.node_id AS to_node, mv.item_key,
         CASE WHEN i.item_type IN ('wort', 'beer', 'product') THEN 'liquid' ELSE i.item_type END
           AS material_class,
         mv.quantity, mv.unit
  FROM movement mv
  JOIN node fn ON fn.node_type = mv.from_node_type AND fn.node_key = mv.from_node_key
  JOIN node tn ON tn.node_type = mv.to_node_type AND tn.node_key = mv.to_node_key
  JOIN item i ON i.item_key = mv.item_key
)
SELECT from_node, to_node, item_key, material_class, quantity, unit,
       quantity / SUM(quantity) OVER (PARTITION BY to_node, material_class) AS share
FROM m;
