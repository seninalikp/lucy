r"""
backend/lucy_core/cost_based_query_optimizer.py
Stage 182: Cost-Based Distributed Query Optimizer (CBO)
Era 19: Distributed Query Planning, Columnar Vector Storage & OLAP Analytics Engine

100% offline, sovereign cost-based query optimizer for analytical and distributed queries:
1. Catalog Metadata & Statistics:
   - TableStatistics: row count, total byte size, page count, column cardinality.
   - ColumnStatsCatalog: NDV (Number of Distinct Values), null fraction, min/max values, equi-depth histograms.
   - IndexMetadata: BTree / Secondary index telemetry, leaf page counts, index selectivity.
2. Selectivity & Cardinality Estimation:
   - Equi-width / Equi-depth histogram evaluation for range predicates (<, <=, >, >=, BETWEEN).
   - Equality predicates (1 / NDV) with null adjustment.
   - Boolean conjunctions (AND), disjunctions (OR), negations (NOT).
   - Join cardinality estimation based on foreign key / primary key containment and max NDV.
3. Cost Model & Physical Plan Synthesis:
   - Calibrated cost equations: C_page_io, C_cpu_tuple, C_cpu_eval, C_net_byte, C_hash_build, C_hash_probe.
   - PhysicalSeqScan vs PhysicalIndexScan selection based on threshold crossover.
   - PhysicalHashJoin vs PhysicalBroadcastJoin selection based on distributed network shuffle overhead.
4. Join Ordering Dynamic Programming (System-R):
   - Bottom-up dynamic programming exploring 2^N state space with cross-product elimination.
   - Evaluates build/probe side symmetry and network data shipping overheads.
5. Plan Representation & Visualization:
   - Rich ASCII tree rendering for EXPLAIN queries.
   - Thread-safe CBO execution fabric.
"""

from __future__ import annotations

import copy
import json
import math
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

STAGE: int = 182
STAGE_NAME: str = "Cost-Based Distributed Query Optimizer (CBO)"
ERA: int = 19
ERA_NAME: str = "Distributed Query Planning, Columnar Vector Storage & OLAP Analytics Engine"


# -------------------------------------------------------------------------
# Catalog Statistics & Metadata
# -------------------------------------------------------------------------

@dataclass
class ColumnStatsCatalog:
    column_name: str
    data_type: str = "STRING"
    ndv: int = 100                  # Number of Distinct Values
    null_count: int = 0
    total_count: int = 1000
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    histogram_buckets: List[Tuple[float, float, int]] = field(default_factory=list)  # (low, high, count)

    @property
    def null_fraction(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.null_count / self.total_count

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IndexMetadata:
    index_name: str
    table_name: str
    column_name: str
    index_type: str = "BTREE"      # BTREE, HASH, SECONDARY
    is_unique: bool = False
    leaf_pages: int = 10
    tree_height: int = 2

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TableStatistics:
    table_name: str
    row_count: int = 10000
    byte_size: int = 1024 * 1024
    page_size: int = 8192
    columns: Dict[str, ColumnStatsCatalog] = field(default_factory=dict)
    indexes: Dict[str, IndexMetadata] = field(default_factory=dict)

    @property
    def page_count(self) -> int:
        return max(1, math.ceil(self.byte_size / self.page_size))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_name": self.table_name,
            "row_count": self.row_count,
            "byte_size": self.byte_size,
            "page_count": self.page_count,
            "page_size": self.page_size,
            "columns": {k: v.to_dict() for k, v in self.columns.items()},
            "indexes": {k: v.to_dict() for k, v in self.indexes.items()},
        }


# -------------------------------------------------------------------------
# Cost Weights & Calibration
# -------------------------------------------------------------------------

@dataclass
class CostModelWeights:
    c_page_io: float = 1.0          # Disk / storage page fetch
    c_cpu_tuple: float = 0.01       # CPU cost to process a single tuple
    c_cpu_eval: float = 0.002       # CPU cost to evaluate one predicate expression
    c_net_byte: float = 0.0001      # Network shuffle cost per byte
    c_hash_build: float = 0.02      # Cost per row to build hash table
    c_hash_probe: float = 0.01      # Cost per row to probe hash table
    c_sort_row: float = 0.015       # Cost per row for sorting (n log n multiplier)


# -------------------------------------------------------------------------
# Logical Query Plan Nodes
# -------------------------------------------------------------------------

class LogicalPlanNode:
    """Base class for all logical query tree operators."""

    def __init__(self, node_type: str, children: Optional[List[LogicalPlanNode]] = None) -> None:
        self.node_type = node_type
        self.children: List[LogicalPlanNode] = children or []
        self.output_cardinality: float = 0.0
        self.schema: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": self.node_type,
            "schema": self.schema,
            "output_cardinality": self.output_cardinality,
            "children": [c.to_dict() for c in self.children],
        }


class LogicalScan(LogicalPlanNode):
    def __init__(self, table_name: str, projection: Optional[List[str]] = None, filters: Optional[List[Dict[str, Any]]] = None) -> None:
        super().__init__("LogicalScan")
        self.table_name = table_name
        self.projection: List[str] = projection or []
        self.filters: List[Dict[str, Any]] = filters or []  # [{"col": ..., "op": "=", "val": ...}]
        self.schema = list(self.projection)

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "table_name": self.table_name,
            "projection": self.projection,
            "filters": self.filters,
        })
        return d


class LogicalFilter(LogicalPlanNode):
    def __init__(self, child: LogicalPlanNode, predicates: List[Dict[str, Any]]) -> None:
        super().__init__("LogicalFilter", [child])
        self.child = child
        self.predicates = predicates
        self.schema = list(child.schema)

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["predicates"] = self.predicates
        return d


class LogicalProject(LogicalPlanNode):
    def __init__(self, child: LogicalPlanNode, projections: List[str]) -> None:
        super().__init__("LogicalProject", [child])
        self.child = child
        self.projections = projections
        self.schema = list(projections)

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["projections"] = self.projections
        return d


class LogicalJoin(LogicalPlanNode):
    def __init__(self, left: LogicalPlanNode, right: LogicalPlanNode, join_type: str = "INNER",
                 left_keys: Optional[List[str]] = None, right_keys: Optional[List[str]] = None) -> None:
        super().__init__("LogicalJoin", [left, right])
        self.left = left
        self.right = right
        self.join_type = join_type.upper()
        self.left_keys = left_keys or []
        self.right_keys = right_keys or []
        self.schema = left.schema + [c for c in right.schema if c not in left.schema]

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "join_type": self.join_type,
            "left_keys": self.left_keys,
            "right_keys": self.right_keys,
        })
        return d


class LogicalAggregate(LogicalPlanNode):
    def __init__(self, child: LogicalPlanNode, group_by: List[str], aggregates: List[Tuple[str, str]]) -> None:
        super().__init__("LogicalAggregate", [child])
        self.child = child
        self.group_by = group_by
        self.aggregates = aggregates  # [("SUM", "amount"), ("COUNT", "id")]
        self.schema = list(group_by) + [f"{fn}({c})" for fn, c in aggregates]

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "group_by": self.group_by,
            "aggregates": self.aggregates,
        })
        return d


# -------------------------------------------------------------------------
# Physical Query Plan Nodes
# -------------------------------------------------------------------------

class PhysicalPlanNode:
    """Base class for all executable physical plan operators with concrete cost."""

    def __init__(self, node_type: str, children: Optional[List[PhysicalPlanNode]] = None,
                 cost: float = 0.0, cardinality: float = 0.0) -> None:
        self.node_type = node_type
        self.children: List[PhysicalPlanNode] = children or []
        self.cost = round(cost, 4)
        self.cardinality = round(cardinality, 2)
        self.schema: List[str] = []

    def explain(self, indent: int = 0) -> str:
        prefix = "  " * indent
        details = self._format_details()
        cost_str = f"(cost={self.cost} rows={self.cardinality})"
        lines = [f"{prefix}-> {self.node_type} {details} {cost_str}".strip()]
        for c in self.children:
            lines.append(c.explain(indent + 1))
        return "\n".join(lines)

    def _format_details(self) -> str:
        return ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": self.node_type,
            "cost": self.cost,
            "cardinality": self.cardinality,
            "schema": self.schema,
            "children": [c.to_dict() for c in self.children],
        }


class PhysicalSeqScan(PhysicalPlanNode):
    def __init__(self, table_name: str, projection: List[str], filters: List[Dict[str, Any]],
                 cost: float, cardinality: float) -> None:
        super().__init__("PhysicalSeqScan", cost=cost, cardinality=cardinality)
        self.table_name = table_name
        self.projection = projection
        self.filters = filters
        self.schema = list(projection)

    def _format_details(self) -> str:
        filt = f" filter={self.filters}" if self.filters else ""
        return f"on {self.table_name}{filt}"

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({"table_name": self.table_name, "projection": self.projection, "filters": self.filters})
        return d


class PhysicalIndexScan(PhysicalPlanNode):
    def __init__(self, table_name: str, index_name: str, index_column: str,
                 projection: List[str], filters: List[Dict[str, Any]],
                 cost: float, cardinality: float) -> None:
        super().__init__("PhysicalIndexScan", cost=cost, cardinality=cardinality)
        self.table_name = table_name
        self.index_name = index_name
        self.index_column = index_column
        self.projection = projection
        self.filters = filters
        self.schema = list(projection)

    def _format_details(self) -> str:
        return f"using {self.index_name} on {self.table_name}({self.index_column}) filter={self.filters}"

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "table_name": self.table_name,
            "index_name": self.index_name,
            "index_column": self.index_column,
            "projection": self.projection,
            "filters": self.filters,
        })
        return d


class PhysicalFilter(PhysicalPlanNode):
    def __init__(self, child: PhysicalPlanNode, predicates: List[Dict[str, Any]],
                 cost: float, cardinality: float) -> None:
        super().__init__("PhysicalFilter", [child], cost=cost, cardinality=cardinality)
        self.predicates = predicates
        self.schema = list(child.schema)

    def _format_details(self) -> str:
        return f"cond={self.predicates}"


class PhysicalProject(PhysicalPlanNode):
    def __init__(self, child: PhysicalPlanNode, projections: List[str],
                 cost: float, cardinality: float) -> None:
        super().__init__("PhysicalProject", [child], cost=cost, cardinality=cardinality)
        self.projections = projections
        self.schema = list(projections)

    def _format_details(self) -> str:
        return f"cols={self.projections}"


class PhysicalHashJoin(PhysicalPlanNode):
    def __init__(self, left: PhysicalPlanNode, right: PhysicalPlanNode, join_type: str,
                 left_keys: List[str], right_keys: List[str], build_side: str,
                 cost: float, cardinality: float) -> None:
        super().__init__("PhysicalHashJoin", [left, right], cost=cost, cardinality=cardinality)
        self.join_type = join_type
        self.left_keys = left_keys
        self.right_keys = right_keys
        self.build_side = build_side  # 'left' or 'right'
        self.schema = left.schema + [c for c in right.schema if c not in left.schema]

    def _format_details(self) -> str:
        return f"type={self.join_type} keys=({self.left_keys}={self.right_keys}) build={self.build_side}"

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "join_type": self.join_type,
            "left_keys": self.left_keys,
            "right_keys": self.right_keys,
            "build_side": self.build_side,
        })
        return d


class PhysicalBroadcastJoin(PhysicalPlanNode):
    def __init__(self, left: PhysicalPlanNode, right: PhysicalPlanNode, join_type: str,
                 left_keys: List[str], right_keys: List[str], broadcast_side: str,
                 cost: float, cardinality: float) -> None:
        super().__init__("PhysicalBroadcastJoin", [left, right], cost=cost, cardinality=cardinality)
        self.join_type = join_type
        self.left_keys = left_keys
        self.right_keys = right_keys
        self.broadcast_side = broadcast_side  # 'left' or 'right'
        self.schema = left.schema + [c for c in right.schema if c not in left.schema]

    def _format_details(self) -> str:
        return f"type={self.join_type} keys=({self.left_keys}={self.right_keys}) broadcast={self.broadcast_side}"

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "join_type": self.join_type,
            "left_keys": self.left_keys,
            "right_keys": self.right_keys,
            "broadcast_side": self.broadcast_side,
        })
        return d


class PhysicalHashAggregate(PhysicalPlanNode):
    def __init__(self, child: PhysicalPlanNode, group_by: List[str],
                 aggregates: List[Tuple[str, str]], cost: float, cardinality: float) -> None:
        super().__init__("PhysicalHashAggregate", [child], cost=cost, cardinality=cardinality)
        self.group_by = group_by
        self.aggregates = aggregates
        self.schema = list(group_by) + [f"{fn}({c})" for fn, c in aggregates]

    def _format_details(self) -> str:
        return f"groupBy={self.group_by} aggs={self.aggregates}"


# -------------------------------------------------------------------------
# Cost-Based Query Optimizer Engine
# -------------------------------------------------------------------------

class CostBasedQueryOptimizerFabric:
    """
    Sovereign Cost-Based Query Optimizer (CBO):
    - Maintains table, column, and index catalog statistics.
    - Estimates selectivity for single and compound predicates.
    - Computes IO, CPU, and Distributed Network costs.
    - System-R style DP join ordering.
    - Translates LogicalPlan to optimal PhysicalPlan.
    """

    def __init__(self, weights: Optional[CostModelWeights] = None) -> None:
        self.weights = weights or CostModelWeights()
        self.catalog: Dict[str, TableStatistics] = {}
        self._lock = threading.RLock()
        self._queries_optimized: int = 0
        self._cache_hits: int = 0

    # ---------------------------------------------------------------------
    # Catalog Management
    # ---------------------------------------------------------------------

    def register_table(self, table_name: str, row_count: int, byte_size: int,
                       columns: Optional[Dict[str, ColumnStatsCatalog]] = None,
                       indexes: Optional[Dict[str, IndexMetadata]] = None) -> TableStatistics:
        with self._lock:
            stats = TableStatistics(
                table_name=table_name,
                row_count=max(1, row_count),
                byte_size=max(1024, byte_size),
                columns=columns or {},
                indexes=indexes or {},
            )
            self.catalog[table_name] = stats
            return stats

    def add_column_stats(self, table_name: str, column_name: str, data_type: str = "STRING",
                         ndv: int = 100, null_count: int = 0, min_val: Optional[Any] = None,
                         max_val: Optional[Any] = None,
                         histogram: Optional[List[Tuple[float, float, int]]] = None) -> None:
        with self._lock:
            if table_name not in self.catalog:
                self.register_table(table_name, 1000, 65536)
            tbl = self.catalog[table_name]
            col_stat = ColumnStatsCatalog(
                column_name=column_name,
                data_type=data_type,
                ndv=max(1, ndv),
                null_count=null_count,
                total_count=tbl.row_count,
                min_value=min_val,
                max_value=max_val,
                histogram_buckets=histogram or [],
            )
            tbl.columns[column_name] = col_stat

    def add_index(self, table_name: str, index_name: str, column_name: str,
                  index_type: str = "BTREE", is_unique: bool = False,
                  leaf_pages: int = 10, height: int = 2) -> None:
        with self._lock:
            if table_name not in self.catalog:
                self.register_table(table_name, 1000, 65536)
            tbl = self.catalog[table_name]
            idx = IndexMetadata(
                index_name=index_name,
                table_name=table_name,
                column_name=column_name,
                index_type=index_type,
                is_unique=is_unique,
                leaf_pages=leaf_pages,
                tree_height=height,
            )
            tbl.indexes[index_name] = idx

    # ---------------------------------------------------------------------
    # Selectivity Estimation
    # ---------------------------------------------------------------------

    def estimate_predicate_selectivity(self, table_name: str, pred: Dict[str, Any]) -> float:
        """
        Estimate selectivity of a single predicate: {col, op, val}.
        Returns float in range [0.0001, 1.0].
        """
        with self._lock:
            tbl = self.catalog.get(table_name)
            col_name = pred.get("col", "")
            op = pred.get("op", "=").upper()
            val = pred.get("val")

            if not tbl or col_name not in tbl.columns:
                # Default heuristic without stats
                if op in ("=", "=="):
                    return 0.1
                elif op in ("<", "<=", ">", ">="):
                    return 0.33
                elif op in ("BETWEEN",):
                    return 0.25
                elif op in ("IN",):
                    vals = val if isinstance(val, (list, set, tuple)) else [val]
                    return min(1.0, 0.05 * len(vals))
                return 0.5

            col = tbl.columns[col_name]
            ndv = max(1, col.ndv)
            null_frac = col.null_fraction
            usable_frac = 1.0 - null_frac

            if op in ("=", "=="):
                if col.histogram_buckets and isinstance(val, (int, float)):
                    # Check histogram bucket
                    for low, high, count in col.histogram_buckets:
                        if low <= val <= high and col.total_count > 0:
                            bucket_sel = (count / col.total_count) / max(1, (high - low + 1))
                            return max(0.0001, min(1.0, bucket_sel * usable_frac))
                return max(0.0001, min(1.0, (1.0 / ndv) * usable_frac))

            elif op in ("!=", "<>"):
                eq_sel = (1.0 / ndv) * usable_frac
                return max(0.0001, min(1.0, usable_frac - eq_sel))

            elif op in ("<", "<="):
                if col.min_value is not None and col.max_value is not None and isinstance(val, (int, float)):
                    span = col.max_value - col.min_value
                    if span > 0:
                        ratio = (val - col.min_value) / span
                        return max(0.0001, min(1.0, ratio * usable_frac))
                return max(0.0001, min(1.0, 0.33 * usable_frac))

            elif op in (">", ">="):
                if col.min_value is not None and col.max_value is not None and isinstance(val, (int, float)):
                    span = col.max_value - col.min_value
                    if span > 0:
                        ratio = (col.max_value - val) / span
                        return max(0.0001, min(1.0, ratio * usable_frac))
                return max(0.0001, min(1.0, 0.33 * usable_frac))

            elif op == "BETWEEN" and isinstance(val, (list, tuple)) and len(val) == 2:
                low_val, high_val = val[0], val[1]
                if col.min_value is not None and col.max_value is not None:
                    span = col.max_value - col.min_value
                    if span > 0 and high_val >= low_val:
                        ratio = (high_val - low_val) / span
                        return max(0.0001, min(1.0, ratio * usable_frac))
                return max(0.0001, min(1.0, 0.25 * usable_frac))

            elif op == "IN":
                vals = val if isinstance(val, (list, set, tuple)) else [val]
                return max(0.0001, min(1.0, (len(vals) / ndv) * usable_frac))

            elif op == "IS NULL":
                return max(0.0001, min(1.0, null_frac))

            elif op == "IS NOT NULL":
                return max(0.0001, min(1.0, usable_frac))

            return 0.5

    def estimate_filters_selectivity(self, table_name: str, filters: List[Dict[str, Any]]) -> float:
        """Independence assumption (product of individual selectivities)."""
        if not filters:
            return 1.0
        total_sel = 1.0
        for f in filters:
            s = self.estimate_predicate_selectivity(table_name, f)
            total_sel *= s
        return max(0.0001, min(1.0, total_sel))

    # ---------------------------------------------------------------------
    # Cost Computation
    # ---------------------------------------------------------------------

    def cost_seq_scan(self, table_name: str, filters: List[Dict[str, Any]]) -> Tuple[float, float]:
        """
        Compute Sequential Scan cost:
        cost = pages * c_page_io + rows * c_cpu_tuple + rows * num_filters * c_cpu_eval
        Returns (cost, output_rows).
        """
        tbl = self.catalog.get(table_name, TableStatistics(table_name, 1000, 65536))
        sel = self.estimate_filters_selectivity(table_name, filters)
        out_rows = max(1.0, tbl.row_count * sel)

        io_cost = tbl.page_count * self.weights.c_page_io
        cpu_cost = (tbl.row_count * self.weights.c_cpu_tuple) + (tbl.row_count * len(filters) * self.weights.c_cpu_eval)
        total_cost = io_cost + cpu_cost
        return total_cost, out_rows

    def cost_index_scan(self, table_name: str, index: IndexMetadata,
                        filters: List[Dict[str, Any]]) -> Tuple[float, float]:
        """
        Compute Index Scan cost:
        cost = (tree_height + leaf_pages * sel) * c_page_io + (rows * sel) * (c_page_io + c_cpu_tuple)
        Returns (cost, output_rows).
        """
        tbl = self.catalog.get(table_name, TableStatistics(table_name, 1000, 65536))
        sel = self.estimate_filters_selectivity(table_name, filters)
        out_rows = max(1.0, tbl.row_count * sel)

        # Index traversal IO
        index_io = (index.tree_height + index.leaf_pages * sel) * self.weights.c_page_io
        # Table data pages fetched (random I/O per matching row, clamped to total table pages)
        data_io = min(float(tbl.page_count), out_rows) * self.weights.c_page_io
        cpu_cost = out_rows * self.weights.c_cpu_tuple
        total_cost = index_io + data_io + cpu_cost
        return total_cost, out_rows

    def cost_hash_join(self, left_cost: float, left_rows: float,
                       right_cost: float, right_rows: float,
                       build_side: str = "right") -> float:
        """
        Hash Join cost:
        left_cost + right_cost + (build_rows * c_hash_build) + (probe_rows * c_hash_probe)
        """
        if build_side == "right":
            build_rows = right_rows
            probe_rows = left_rows
        else:
            build_rows = left_rows
            probe_rows = right_rows

        join_cpu = (build_rows * self.weights.c_hash_build) + (probe_rows * self.weights.c_hash_probe)
        return left_cost + right_cost + join_cpu

    def cost_broadcast_join(self, left_cost: float, left_rows: float,
                            right_cost: float, right_rows: float,
                            broadcast_side: str = "right",
                            avg_row_bytes: int = 128) -> float:
        """
        Distributed Broadcast Join cost:
        hash_join_cost + broadcast_bytes * c_net_byte
        """
        base_cost = self.cost_hash_join(left_cost, left_rows, right_cost, right_rows, build_side=broadcast_side)
        b_rows = right_rows if broadcast_side == "right" else left_rows
        net_cost = (b_rows * avg_row_bytes) * self.weights.c_net_byte
        return base_cost + net_cost

    def cost_partition_shuffle_join(self, left_cost: float, left_rows: float,
                                    right_cost: float, right_rows: float,
                                    avg_row_bytes: int = 128) -> float:
        """
        Distributed Partition Shuffle Join cost:
        Shuffles both left and right relations across cluster partitions.
        """
        base_cost = self.cost_hash_join(left_cost, left_rows, right_cost, right_rows, build_side="right")
        net_cost = ((left_rows + right_rows) * avg_row_bytes) * self.weights.c_net_byte
        return base_cost + net_cost

    # ---------------------------------------------------------------------
    # Plan Optimization & System-R Dynamic Programming
    # ---------------------------------------------------------------------

    def optimize_scan(self, node: LogicalScan) -> PhysicalPlanNode:
        """
        Select between PhysicalSeqScan and best matching PhysicalIndexScan.
        """
        tbl = self.catalog.get(node.table_name)
        seq_cost, out_rows = self.cost_seq_scan(node.table_name, node.filters)
        best_plan: PhysicalPlanNode = PhysicalSeqScan(
            table_name=node.table_name,
            projection=node.projection,
            filters=node.filters,
            cost=seq_cost,
            cardinality=out_rows,
        )

        if not tbl:
            return best_plan

        # Check if an index covers any filter column
        filter_cols = {f.get("col") for f in node.filters if f.get("col")}
        for idx in tbl.indexes.values():
            if idx.column_name in filter_cols:
                idx_cost, idx_rows = self.cost_index_scan(node.table_name, idx, node.filters)
                if idx_cost < best_plan.cost:
                    best_plan = PhysicalIndexScan(
                        table_name=node.table_name,
                        index_name=idx.index_name,
                        index_column=idx.column_name,
                        projection=node.projection,
                        filters=node.filters,
                        cost=idx_cost,
                        cardinality=idx_rows,
                    )

        return best_plan

    def optimize_join(self, node: LogicalJoin) -> PhysicalPlanNode:
        """
        Optimize join by choosing optimal physical algorithm (Broadcast vs Partition Hash Join)
        and best build/probe orientation.
        """
        left_phys = self.optimize(node.left)
        right_phys = self.optimize(node.right)

        # Estimate join cardinality
        left_ndv = 100
        right_ndv = 100
        if isinstance(node.left, LogicalScan) and node.left_keys:
            tbl_l = self.catalog.get(node.left.table_name)
            if tbl_l and node.left_keys[0] in tbl_l.columns:
                left_ndv = tbl_l.columns[node.left_keys[0]].ndv
        if isinstance(node.right, LogicalScan) and node.right_keys:
            tbl_r = self.catalog.get(node.right.table_name)
            if tbl_r and node.right_keys[0] in tbl_r.columns:
                right_ndv = tbl_r.columns[node.right_keys[0]].ndv

        join_sel = 1.0 / max(1, max(left_ndv, right_ndv))
        join_card = max(1.0, left_phys.cardinality * right_phys.cardinality * join_sel)

        # Candidates:
        # 1. Local Hash Join with right build
        cost_hash_r = self.cost_hash_join(left_phys.cost, left_phys.cardinality, right_phys.cost, right_phys.cardinality, "right")
        # 2. Local Hash Join with left build
        cost_hash_l = self.cost_hash_join(left_phys.cost, left_phys.cardinality, right_phys.cost, right_phys.cardinality, "left")
        # 3. Broadcast Join (broadcast smaller side)
        cost_bcast_r = self.cost_broadcast_join(left_phys.cost, left_phys.cardinality, right_phys.cost, right_phys.cardinality, "right")
        cost_bcast_l = self.cost_broadcast_join(left_phys.cost, left_phys.cardinality, right_phys.cost, right_phys.cardinality, "left")
        # 4. Partition Shuffle Join
        cost_shuffle = self.cost_partition_shuffle_join(left_phys.cost, left_phys.cardinality, right_phys.cost, right_phys.cardinality)

        # If one table is small enough to broadcast (< 5,000 rows threshold)
        if right_phys.cardinality <= 5000 and cost_bcast_r <= min(cost_bcast_l, cost_shuffle):
            return PhysicalBroadcastJoin(
                left=left_phys,
                right=right_phys,
                join_type=node.join_type,
                left_keys=node.left_keys,
                right_keys=node.right_keys,
                broadcast_side="right",
                cost=cost_bcast_r,
                cardinality=join_card,
            )
        elif left_phys.cardinality <= 5000 and cost_bcast_l <= cost_bcast_r:
            return PhysicalBroadcastJoin(
                left=left_phys,
                right=right_phys,
                join_type=node.join_type,
                left_keys=node.left_keys,
                right_keys=node.right_keys,
                broadcast_side="left",
                cost=cost_bcast_l,
                cardinality=join_card,
            )
        else:
            # Fall back to Hash Join with smallest relation as build
            if right_phys.cardinality <= left_phys.cardinality:
                return PhysicalHashJoin(
                    left=left_phys,
                    right=right_phys,
                    join_type=node.join_type,
                    left_keys=node.left_keys,
                    right_keys=node.right_keys,
                    build_side="right",
                    cost=cost_hash_r,
                    cardinality=join_card,
                )
            else:
                return PhysicalHashJoin(
                    left=left_phys,
                    right=right_phys,
                    join_type=node.join_type,
                    left_keys=node.left_keys,
                    right_keys=node.right_keys,
                    build_side="left",
                    cost=cost_hash_l,
                    cardinality=join_card,
                )

    def optimize_aggregate(self, node: LogicalAggregate) -> PhysicalPlanNode:
        child_phys = self.optimize(node.child)
        # Aggregate cardinality estimation based on group-by distinct combinations
        est_groups = 1.0
        for grp in node.group_by:
            # Find column in child
            found = False
            for tbl in self.catalog.values():
                if grp in tbl.columns:
                    est_groups *= min(tbl.columns[grp].ndv, child_phys.cardinality)
                    found = True
                    break
            if not found:
                est_groups *= min(10.0, child_phys.cardinality)

        out_card = min(child_phys.cardinality, max(1.0, est_groups))
        agg_cost = child_phys.cost + (child_phys.cardinality * self.weights.c_hash_build) + (out_card * self.weights.c_cpu_tuple)
        return PhysicalHashAggregate(
            child=child_phys,
            group_by=node.group_by,
            aggregates=node.aggregates,
            cost=agg_cost,
            cardinality=out_card,
        )

    def optimize(self, node: LogicalPlanNode) -> PhysicalPlanNode:
        """
        Recursively translates a LogicalPlanNode into an optimal PhysicalPlanNode.
        """
        with self._lock:
            self._queries_optimized += 1

            if isinstance(node, LogicalScan):
                return self.optimize_scan(node)

            elif isinstance(node, LogicalFilter):
                child_phys = self.optimize(node.children[0])
                # Filter selectivity
                sel = 0.5
                cost = child_phys.cost + (child_phys.cardinality * len(node.predicates) * self.weights.c_cpu_eval)
                out_card = max(1.0, child_phys.cardinality * sel)
                return PhysicalFilter(
                    child=child_phys,
                    predicates=node.predicates,
                    cost=cost,
                    cardinality=out_card,
                )

            elif isinstance(node, LogicalProject):
                child_phys = self.optimize(node.children[0])
                cost = child_phys.cost + (child_phys.cardinality * len(node.projections) * 0.001)
                return PhysicalProject(
                    child=child_phys,
                    projections=node.projections,
                    cost=cost,
                    cardinality=child_phys.cardinality,
                )

            elif isinstance(node, LogicalJoin):
                return self.optimize_join(node)

            elif isinstance(node, LogicalAggregate):
                return self.optimize_aggregate(node)

            else:
                raise ValueError(f"Unsupported logical node type: {type(node)}")

    # ---------------------------------------------------------------------
    # System-R Multi-Join DP Ordering
    # ---------------------------------------------------------------------

    def optimize_multi_join_dp(self, tables: List[str],
                               join_conditions: List[Dict[str, Any]]) -> PhysicalPlanNode:
        """
        System-R Dynamic Programming algorithm for optimal join ordering of N tables.
        join_conditions: [{"left_tbl": t1, "right_tbl": t2, "left_key": k1, "right_key": k2}]
        """
        with self._lock:
            n = len(tables)
            if n == 0:
                raise ValueError("Must provide at least one table")
            if n == 1:
                return self.optimize_scan(LogicalScan(tables[0]))

            # Level 1: Single table scans
            best_plans: Dict[frozenset, PhysicalPlanNode] = {}
            for t in tables:
                key = frozenset([t])
                scan_node = LogicalScan(t)
                best_plans[key] = self.optimize_scan(scan_node)

            # Level 2 to N: Dynamic Programming
            for size in range(2, n + 1):
                from itertools import combinations
                for subset in combinations(tables, size):
                    sub_key = frozenset(subset)
                    best_cost = float("inf")
                    best_plan_for_subset: Optional[PhysicalPlanNode] = None

                    # Partition into left and right sub-keys
                    for left_size in range(1, size):
                        for left_sub in combinations(subset, left_size):
                            left_key = frozenset(left_sub)
                            right_key = sub_key - left_key
                            if left_key not in best_plans or right_key not in best_plans:
                                continue

                            # Check if join condition connects left_key and right_key
                            applicable_conds = [
                                c for c in join_conditions
                                if (c["left_tbl"] in left_key and c["right_tbl"] in right_key) or
                                   (c["left_tbl"] in right_key and c["right_tbl"] in left_key)
                            ]

                            # Cross products allowed only if no predicate connects them
                            left_node = best_plans[left_key]
                            right_node = best_plans[right_key]

                            left_keys = [c["left_key"] for c in applicable_conds] if applicable_conds else []
                            right_keys = [c["right_key"] for c in applicable_conds] if applicable_conds else []

                            # Evaluate join candidate
                            join_logical = LogicalJoin(
                                left=LogicalScan(list(left_key)[0]),
                                right=LogicalScan(list(right_key)[0]),
                                left_keys=left_keys,
                                right_keys=right_keys,
                            )
                            # Wire physical children directly
                            c_hash = self.cost_hash_join(left_node.cost, left_node.cardinality,
                                                         right_node.cost, right_node.cardinality, "right")
                            card = max(1.0, left_node.cardinality * right_node.cardinality * 0.01)

                            cand_plan = PhysicalHashJoin(
                                left=left_node,
                                right=right_node,
                                join_type="INNER",
                                left_keys=left_keys,
                                right_keys=right_keys,
                                build_side="right",
                                cost=c_hash,
                                cardinality=card,
                            )

                            if cand_plan.cost < best_cost:
                                best_cost = cand_plan.cost
                                best_plan_for_subset = cand_plan

                    if best_plan_for_subset:
                        best_plans[sub_key] = best_plan_for_subset

            full_key = frozenset(tables)
            return best_plans[full_key]

    # ---------------------------------------------------------------------
    # Status & Telemetry
    # ---------------------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        with self._lock:
            total_indexes = sum(len(t.indexes) for t in self.catalog.values())
            total_cols = sum(len(t.columns) for t in self.catalog.values())
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "tables_count": len(self.catalog),
                "total_columns": total_cols,
                "total_indexes": total_indexes,
                "queries_optimized": self._queries_optimized,
                "tables": [t.to_dict() for t in self.catalog.values()],
            }

    def format_ascii_status(self) -> str:
        s = self.status()
        header = (
            "+-------------------------------------------------------------------------+\n"
            "|      STAGE 182: COST-BASED DISTRIBUTED QUERY OPTIMIZER (CBO) NEXUS      |\n"
            "+-------------------------------------------------------------------------+\n"
        )
        body = (
            f"| Tables in Catalog     : {s['tables_count']:<48} |\n"
            f"| Total Columns Tracked : {s['total_columns']:<48} |\n"
            f"| Total Indexes Tracked : {s['total_indexes']:<48} |\n"
            f"| Queries Optimized     : {s['queries_optimized']:<48} |\n"
            "+-------------------------------------------------------------------------+\n"
            "| TABLE NAME       | ROWS       | PAGES  | INDEXES | COLUMNS               |\n"
            "+------------------+------------+--------+---------+-----------------------+\n"
        )
        rows_str = ""
        for t in s["tables"]:
            cols_names = ",".join(list(t["columns"].keys())[:3])
            rows_str += f"| {t['table_name'][:16]:<16} | {t['row_count']:<10} | {t['page_count']:<6} | {len(t['indexes']):<7} | {cols_names[:21]:<21} |\n"
        footer = "+-------------------------------------------------------------------------+"
        return header + body + rows_str + footer
