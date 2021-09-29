"""
Import as:

import core.features as ftrs
"""

import collections
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

import helpers.dbg as dbg

_LOG = logging.getLogger(__name__)


def get_lagged_feature_names(
    y_var: str, delay_lag: int, num_lags: int
) -> Tuple[List[int], List[str]]:
    dbg.dassert(
        y_var.endswith("_0"),
        "y_var='%s' is not a valid name to generate lagging variables",
        y_var,
    )
    if delay_lag < 1:
        _LOG.warning(
            "Using anticausal features since delay_lag=%d < 1. This "
            "could be lead to future peeking",
            delay_lag,
        )
    dbg.dassert_lte(1, num_lags)
    #
    x_var_shifts = list(range(1 + delay_lag, 1 + delay_lag + num_lags))
    x_vars = []
    for i in x_var_shifts:
        x_var = y_var.replace("_0", "_%d" % i)
        x_vars.append(x_var)
    dbg.dassert_eq(len(x_vars), len(x_var_shifts))
    return x_var_shifts, x_vars


def compute_lagged_features(
    df: pd.DataFrame, y_var: str, delay_lag: int, num_lags: int
) -> Tuple[pd.DataFrame, collections.OrderedDict]:
    """
    Compute features by adding lags of `y_var` in `df`. The operation is
    performed in-place.

    :return: transformed df and info about the transformation.
    """
    info = collections.OrderedDict()
    dbg.dassert_in(y_var, df.columns)
    _LOG.debug("df.shape=%s", df.shape)
    #
    _LOG.debug("y_var='%s'", y_var)
    info["y_var"] = y_var
    x_var_shifts, x_vars = get_lagged_feature_names(y_var, delay_lag, num_lags)
    _LOG.debug("x_vars=%s", x_vars)
    info["x_vars"] = x_vars
    for i, num_shifts in enumerate(x_var_shifts):
        x_var = x_vars[i]
        _LOG.debug("Computing var=%s", x_var)
        df[x_var] = df[y_var].shift(num_shifts)
    # TODO(gp): Add dropna stats using exp.dropna().
    info["before_df.shape"] = df.shape
    df = df.dropna()
    _LOG.debug("df.shape=%s", df.shape)
    info["after_df.shape"] = df.shape
    return df, info


def compute_lagged_columns(
    df: pd.DataFrame, lag_delay: int, num_lags: int
) -> pd.DataFrame:
    """
    Compute lags of each column in df.
    """
    out_cols = []
    dbg.dassert_isinstance(df, pd.DataFrame)
    for col in df.columns:
        out_col = compute_lags(df[col], lag_delay, num_lags)
        out_col.rename(columns=lambda x: str(col) + "_" + x, inplace=True)
        out_cols.append(out_col)
    return pd.concat(out_cols, axis=1)


def compute_lags(srs: pd.Series, lag_delay: int, num_lags: int) -> pd.DataFrame:
    """
    Compute `num_lags` lags of `srs` starting with a delay of `lag_delay`.
    """
    if lag_delay < 0:
        _LOG.warning(
            "Using anticausal features since lag_delay=%d < 0. This "
            "could lead to future peeking.",
            lag_delay,
        )
    dbg.dassert_lte(1, num_lags)
    #
    shifts = list(range(1 + lag_delay, 1 + lag_delay + num_lags))
    out_cols = []
    dbg.dassert_isinstance(srs, pd.Series)
    for num_shifts in shifts:
        out_col = srs.shift(num_shifts)
        out_col.name = "lag%i" % num_shifts
        out_cols.append(out_col)
    return pd.concat(out_cols, axis=1)


def combine_columns(
    df: pd.DataFrame,
    term1_col: Union[str, int],
    term2_col: Union[str, int],
    out_col: Union[str, int],
    operation: str,
    arithmetic_kwargs: Optional[Dict[str, Any]] = None,
    term1_delay: Optional[int] = 0,
    term2_delay: Optional[int] = 0,
) -> pd.DataFrame:
    """
    Apply an arithmetic operation to two columns.

    :param df: input data
    :param term1_col: name of col for `term1` in `term1.operation(term2)`
    :param term2_col: name of col for `term2`
    :param out_col: name of dataframe column with result
    :param operation: "add", "sub", "mul", or "div"
    :param arithmetic_kwargs: kwargs for `operation()`
    :param term1_delay: number of shifts to preapply to term1
    :param term2_delay: number of shifts to preapply to term2
    :return: 1-column dataframe with result of binary operation
    """
    dbg.dassert_in(term1_col, df.columns.to_list())
    dbg.dassert_in(term2_col, df.columns.to_list())
    dbg.dassert_not_in(out_col, df.columns.to_list())
    dbg.dassert_in(operation, ["add", "sub", "mul", "div"])
    arithmetic_kwargs = arithmetic_kwargs or {}
    #
    term1 = df[term1_col].shift(term1_delay)
    term2 = df[term2_col].shift(term2_delay)
    result = getattr(term1, operation)(term2, **arithmetic_kwargs)
    result.name = out_col
    #
    return result.to_frame()
