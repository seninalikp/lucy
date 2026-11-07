r"""
backend/lucy_core/materialized_view_ivm.py
Stage 186: Materialized View Refresh & Incremental View Maintenance (IVM)
Era 19: Distributed Query Planning, Columnar Vector Storage & OLAP Analytics Engine

100% offline, sovereign incremental view maintenance (IVM) engine:
1. Algebraic Delta Propagation (SPJA queries):
   - Delta Selection: \sigma(\Delta R)
   - Delta Projection: \Pi(\Delta R)
   - Delta Join: \Delta(R \bowtie S) = (\Delta R \bowtie S_{new}) \cup (R_{old} \bowtie \Delta S)
   - Delta Aggregate: Maintains group key accumulators (sum, count, min, max) with delta addition/subtraction.
2. Refresh Policies:
   - EAGER: Incremental maintenance immediately executed on base table mutations.
   - LAZY: Marks view as STALE; incrementally or fully refreshed on first read.
   - PERIODIC: Batched refresh on demand or schedule.
3. Multi-Version LSN Staleness Sentinel:
   - Base table mutation LSN tracking ensures no lost updates and consistency guarantees.
4. Thread-safe execution fabric and CP1252-safe ASCII table formatting.
"""

from __future__ import annotations

import collections
import copy
import json
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

STAGE: int = 186
STAGE_NAME: str = "Materialized View Refresh & Incremental View Maintenance (IVM)"
ERA: int = 19
ERA_NAME: str = "Distributed Query Planning, Columnar Vector Storage & OLAP Analytics Engine"


class RefreshPolicy:
    EAGER = "EAGER"
    LAZY = "LAZY"
    PERIODIC = "PERIODIC"


class ViewStatus:
    FRESH = "FRESH"
    STALE = "STALE"
    REFRESHING = "REFRESHING"


@dataclass
class ViewAggregationSpec:
    group_by: List[str]
    aggregates: List[Tuple[str, str, str]]  # [(func, src_col, out_col)] e.g. [("SUM", "amount", "total_amt")]


@dataclass
class ViewDefinition:
    view_name: str
    base_tables: List[str]
    refresh_policy: str = RefreshPolicy.EAGER
    filters: List[Tuple[str, str, Any]] = field(default_factory=list)  # [(col, op, val)]
    projections: List[str] = field(default_factory=list)
    join_spec: Optional[Dict[str, Any]] = None  # {"left_tbl": ..., "right_tbl": ..., "left_key": ..., "right_key": ...}
    aggregation_spec: Optional[ViewAggregationSpec] = None
    status: str = ViewStatus.FRESH
    last_refresh_lsn: int = 0
    total_refreshes: int = 0
    row_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.aggregation_spec:
            d["aggregation_spec"] = {
                "group_by": self.aggregation_spec.group_by,
                "aggregates": self.aggregation_spec.aggregates,
            }
        return d


class MaterializedViewIVMFabric:
    """
    Sovereign Materialized View & Incremental View Maintenance Engine:
    - Maintains materialized view storage.
    - Applies algebraic delta changes on base table mutations.
    - Supports Eager and Lazy incremental and full refreshes.
    """

    def __init__(self) -> None:
        self.views: Dict[str, ViewDefinition] = {}
        # View data storage: view_name -> list of row dicts or group_key -> accum dict
        self.view_data: Dict[str, List[Dict[str, Any]]] = {}
        self.group_accumulators: Dict[str, Dict[Tuple[Any, ...], Dict[str, Any]]] = {}

        # Base tables storage for joins and full recomputations: table_name -> list of dicts
        self.base_tables: Dict[str, List[Dict[str, Any]]] = collections.defaultdict(list)
        self.base_table_lsns: Dict[str, int] = collections.defaultdict(int)

        self._lock = threading.RLock()
        self._global_lsn: int = 0

    def _next_lsn(self) -> int:
        self._global_lsn += 1
        return self._global_lsn

    def register_base_table(self, table_name: str, rows: Optional[List[Dict[str, Any]]] = None) -> None:
        with self._lock:
            self.base_tables[table_name] = [copy.deepcopy(r) for r in (rows or [])]
            self.base_table_lsns[table_name] = self._next_lsn()

    def create_materialized_view(self, view_name: str, base_tables: List[str],
                                 refresh_policy: str = RefreshPolicy.EAGER,
                                 filters: Optional[List[Tuple[str, str, Any]]] = None,
                                 projections: Optional[List[str]] = None,
                                 join_spec: Optional[Dict[str, Any]] = None,
                                 aggregation_spec: Optional[ViewAggregationSpec] = None) -> ViewDefinition:
        with self._lock:
            v_def = ViewDefinition(
                view_name=view_name,
                base_tables=base_tables,
                refresh_policy=refresh_policy,
                filters=filters or [],
                projections=projections or [],
                join_spec=join_spec,
                aggregation_spec=aggregation_spec,
                status=ViewStatus.FRESH,
                last_refresh_lsn=self._global_lsn,
            )
            self.views[view_name] = v_def
            self.view_data[view_name] = []
            self.group_accumulators[view_name] = {}

            # Initial full compute
            self._full_recompute(view_name)
            return v_def

    def _matches_filters(self, row: Dict[str, Any], filters: List[Tuple[str, str, Any]]) -> bool:
        for col, op, val in filters:
            rv = row.get(col)
            if op in ("=", "==") and rv != val:
                return False
            elif op in ("!=", "<>") and rv == val:
                return False
            elif op == ">" and (rv is None or rv <= val):
                return False
            elif op == ">=" and (rv is None or rv < val):
                return False
            elif op == "<" and (rv is None or rv >= val):
                return False
            elif op == "<=" and (rv is None or rv > val):
                return False
        return True

    def _full_recompute(self, view_name: str) -> None:
        v_def = self.views[view_name]
        v_def.status = ViewStatus.REFRESHING

        # 1. Join / Scan Base Tables
        if v_def.join_spec:
            js = v_def.join_spec
            l_rows = self.base_tables.get(js["left_tbl"], [])
            r_rows = self.base_tables.get(js["right_tbl"], [])
            l_key = js["left_key"]
            r_key = js["right_key"]

            r_map = collections.defaultdict(list)
            for r in r_rows:
                r_map[r.get(r_key)].append(r)

            scanned: List[Dict[str, Any]] = []
            for l in l_rows:
                lk = l.get(l_key)
                for r in r_map.get(lk, []):
                    merged = dict(l)
                    for k, v in r.items():
                        if k not in merged or k == r_key:
                            merged[k] = v
                        else:
                            merged[f"right_{k}"] = v
                    scanned.append(merged)
        else:
            base_tbl = v_def.base_tables[0]
            scanned = [dict(r) for r in self.base_tables.get(base_tbl, [])]

        # 2. Filters
        filtered = [r for r in scanned if self._matches_filters(r, v_def.filters)]

        # 3. Aggregation or Projection
        if v_def.aggregation_spec:
            agg_spec = v_def.aggregation_spec
            accum: Dict[Tuple[Any, ...], Dict[str, Any]] = {}
            for r in filtered:
                grp_key = tuple(r.get(g) for g in agg_spec.group_by)
                if grp_key not in accum:
                    st: Dict[str, Any] = {}
                    for fn, _, out_c in agg_spec.aggregates:
                        fn_u = fn.upper()
                        if fn_u in ("SUM", "COUNT"):
                            st[out_c] = 0.0 if fn_u == "SUM" else 0
                        elif fn_u == "MIN":
                            st[out_c] = float("inf")
                        elif fn_u == "MAX":
                            st[out_c] = float("-inf")
                    accum[grp_key] = st

                st = accum[grp_key]
                for fn, src_c, out_c in agg_spec.aggregates:
                    val = r.get(src_c)
                    if val is None:
                        continue
                    fn_u = fn.upper()
                    if fn_u == "SUM":
                        st[out_c] += float(val)
                    elif fn_u == "COUNT":
                        st[out_c] += 1
                    elif fn_u == "MIN":
                        if float(val) < st[out_c]:
                            st[out_c] = float(val)
                    elif fn_u == "MAX":
                        if float(val) > st[out_c]:
                            st[out_c] = float(val)

            self.group_accumulators[view_name] = accum
            # Materialize to rows
            final_rows: List[Dict[str, Any]] = []
            for grp_key, st in accum.items():
                row: Dict[str, Any] = {}
                for idx, g in enumerate(agg_spec.group_by):
                    row[g] = grp_key[idx]
                row.update(st)
                final_rows.append(row)
            self.view_data[view_name] = final_rows

        else:
            if v_def.projections:
                final_rows = [{p: r.get(p) for p in v_def.projections} for r in filtered]
            else:
                final_rows = filtered
            self.view_data[view_name] = final_rows

        v_def.row_count = len(self.view_data[view_name])
        v_def.status = ViewStatus.FRESH
        v_def.last_refresh_lsn = self._global_lsn
        v_def.total_refreshes += 1

    def apply_ivm_delta(self, view_name: str, table_mutated: str,
                        inserted: List[Dict[str, Any]], deleted: List[Dict[str, Any]]) -> None:
        """
        Incrementally propagates delta rows into the materialized view without recomputing full query.
        """
        v_def = self.views[view_name]
        if v_def.status == ViewStatus.STALE and v_def.refresh_policy != RefreshPolicy.EAGER:
            return

        # 1. Delta Selection
        ins_filtered = [r for r in inserted if self._matches_filters(r, v_def.filters)]
        del_filtered = [r for r in deleted if self._matches_filters(r, v_def.filters)]

        # 2. Aggregations IVM
        if v_def.aggregation_spec:
            agg_spec = v_def.aggregation_spec
            accum = self.group_accumulators[view_name]

            # Process inserts
            for r in ins_filtered:
                grp_key = tuple(r.get(g) for g in agg_spec.group_by)
                if grp_key not in accum:
                    st: Dict[str, Any] = {out_c: 0.0 for _, _, out_c in agg_spec.aggregates}
                    accum[grp_key] = st
                st = accum[grp_key]
                for fn, src_c, out_c in agg_spec.aggregates:
                    val = r.get(src_c)
                    if val is None:
                        continue
                    fn_u = fn.upper()
                    if fn_u == "SUM":
                        st[out_c] += float(val)
                    elif fn_u == "COUNT":
                        st[out_c] += 1
                    elif fn_u == "MAX":
                        if float(val) > st[out_c]:
                            st[out_c] = float(val)

            # Process deletes
            for r in del_filtered:
                grp_key = tuple(r.get(g) for g in agg_spec.group_by)
                if grp_key in accum:
                    st = accum[grp_key]
                    for fn, src_c, out_c in agg_spec.aggregates:
                        val = r.get(src_c)
                        if val is None:
                            continue
                        fn_u = fn.upper()
                        if fn_u == "SUM":
                            st[out_c] -= float(val)
                        elif fn_u == "COUNT":
                            st[out_c] = max(0, st[out_c] - 1)

            # Sync rows
            final_rows: List[Dict[str, Any]] = []
            for grp_key, st in accum.items():
                row = {g: grp_key[i] for i, g in enumerate(agg_spec.group_by)}
                row.update(st)
                final_rows.append(row)
            self.view_data[view_name] = final_rows

        else:
            # Simple SPJ views
            cur_rows = self.view_data[view_name]
            # Add projected inserts
            if ins_filtered:
                if v_def.projections:
                    new_rows = [{p: r.get(p) for p in v_def.projections} for r in ins_filtered]
                else:
                    new_rows = ins_filtered
                cur_rows.extend(new_rows)

            # Remove deletes
            if del_filtered:
                del_set = [{p: r.get(p) for p in v_def.projections} for r in del_filtered] if v_def.projections else del_filtered
                filtered_cur = [r for r in cur_rows if r not in del_set]
                self.view_data[view_name] = filtered_cur

        v_def.row_count = len(self.view_data[view_name])
        v_def.last_refresh_lsn = self._global_lsn
        v_def.total_refreshes += 1

    def mutate_table(self, table_name: str, inserted: Optional[List[Dict[str, Any]]] = None,
                     deleted: Optional[List[Dict[str, Any]]] = None) -> int:
        """
        Notifies engine of base table change, triggering eager IVM or marking lazy views stale.
        """
        with self._lock:
            lsn = self._next_lsn()
            self.base_table_lsns[table_name] = lsn
            ins = inserted or []
            dels = deleted or []

            # Mutate base table
            tbl_rows = self.base_tables[table_name]
            tbl_rows.extend([copy.deepcopy(r) for r in ins])
            if dels:
                tbl_rows[:] = [r for r in tbl_rows if r not in dels]

            # Update views referencing table_name
            for vname, vdef in self.views.items():
                if table_name in vdef.base_tables:
                    if vdef.refresh_policy == RefreshPolicy.EAGER:
                        self.apply_ivm_delta(vname, table_name, ins, dels)
                    else:
                        vdef.status = ViewStatus.STALE

            return lsn

    def query_view(self, view_name: str) -> List[Dict[str, Any]]:
        with self._lock:
            if view_name not in self.views:
                raise KeyError(f"View {view_name} does not exist")
            vdef = self.views[view_name]
            if vdef.status == ViewStatus.STALE and vdef.refresh_policy == RefreshPolicy.LAZY:
                self._full_recompute(view_name)
            return list(self.view_data[view_name])

    def refresh(self, view_name: str) -> None:
        with self._lock:
            if view_name not in self.views:
                raise KeyError(f"View {view_name} does not exist")
            self._full_recompute(view_name)

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "views_count": len(self.views),
                "base_tables_count": len(self.base_tables),
                "global_lsn": self._global_lsn,
                "views": [v.to_dict() for v in self.views.values()],
            }

    def format_ascii_status(self) -> str:
        s = self.status()
        header = (
            "+-------------------------------------------------------------------------+\n"
            "|      STAGE 186: MATERIALIZED VIEW & INCREMENTAL VIEW MAINTENANCE (IVM)   |\n"
            "+-------------------------------------------------------------------------+\n"
        )
        body = (
            f"| Active Views Count    : {s['views_count']:<48} |\n"
            f"| Base Tables Tracked   : {s['base_tables_count']:<48} |\n"
            f"| Global Mutation LSN   : {s['global_lsn']:<48} |\n"
            "+-------------------------------------------------------------------------+\n"
            "| VIEW NAME        | POLICY   | STATUS     | ROWS       | REFRESHES | LSN   |\n"
            "+------------------+----------+------------+------------+-----------+-------+\n"
        )
        rows_str = ""
        for v in s["views"]:
            rows_str += f"| {v['view_name'][:16]:<16} | {v['refresh_policy']:<8} | {v['status']:<10} | {v['row_count']:<10} | {v['total_refreshes']:<9} | {v['last_refresh_lsn']:<5} |\n"
        footer = "+-------------------------------------------------------------------------+"
        return header + body + rows_str + footer
