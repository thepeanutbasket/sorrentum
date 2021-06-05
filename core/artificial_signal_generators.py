"""
Import as:

import core.artificial_signal_generators as sig_gen
"""

import logging
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import scipy as sp

# import statsmodels as sm
import statsmodels.api as sm

import helpers.dbg as dbg

# TODO(*): statsmodels needs this import to work properly.
# import statsmodels.tsa.arima_process as smarima  # isort: skip # noqa: F401 # pylint: disable=unused-import


_LOG = logging.getLogger(__name__)

# TODO(gp): Remove after PTask2335.
if True:
    import gluonts
    import gluonts.dataset.artificial as gda
    import gluonts.dataset.artificial.recipe as rcp

    import gluonts.dataset.repository.datasets as gdrd  # isort: skip # noqa: F401 # pylint: disable=unused-import
    import gluonts.dataset.util as gdu  # isort: skip # noqa: F401 # pylint: disable=unused-import

    def get_gluon_dataset_names() -> List[str]:
        """
        Get names of available Gluon datasets. Each of those names can be used
        in `get_gluon_dataset` function.

        :return: list of names
        """
        return list(gluonts.dataset.repository.datasets.dataset_recipes.keys())

    def get_gluon_dataset(
        dataset_name: str = "m4_hourly",
        train_length: Optional[int] = None,
        test_length: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load Gluon dataset, transform it into train and test dataframes.

        The default `m4_hourly` time series look like this:
        https://gluon-ts.mxnet.io/_images/examples_forecasting_tutorial_9_0.png

        :param dataset_name: name of the dataset. Supported names can be
            obtained using `get_gluon_dataset_names`.
        :param train_length: length of the train dataset
        :param test_length: length of the test dataset
        :return: train and test dataframes
        """
        dataset = gluonts.dataset.repository.datasets.get_dataset(
            dataset_name, regenerate=False
        )
        train_entry = next(iter(dataset.train))
        test_entry = next(iter(dataset.test))
        train_df = gluonts.dataset.util.to_pandas(train_entry)
        test_df = gluonts.dataset.util.to_pandas(test_entry)
        train_length = train_length or train_df.shape[0]
        test_length = test_length or test_df.shape[0]
        dbg.dassert_lte(train_length, train_df.shape[0])
        dbg.dassert_lte(test_length, test_df.shape[0])
        train_df = pd.DataFrame(train_df.head(train_length), columns=["y"])
        test_df = pd.DataFrame(test_df.head(test_length), columns=["y"])
        return train_df, test_df

    def evaluate_recipe(
        recipe: List[Tuple[str, Callable]], length: int, **kwargs: Any
    ) -> Dict[str, np.array]:
        """
        Generate data based on recipe.

        For documentation on recipes, see
        https://gluon-ts.mxnet.io/_modules/gluonts/dataset/artificial/_base.html#RecipeDataset.

        :param recipe: [(field, function)]
        :param length: length of data to generate
        :param kwargs: kwargs passed into gluonts.dataset.artificial.recipe.evaluate
        :return: field names mapped to generated data
        """
        return rcp.evaluate(recipe, length, **kwargs)

    def add_recipe_components(
        recipe: List[Tuple[str, Callable]], name: str = "signal"
    ) -> List[Tuple[str, rcp.Lifted]]:
        """
        Append the sum of the components to the recipe.

        :param recipe: [(field, function)]
        :param name: name of the sum
        :return: recipe with the sum component
        """
        recipe = recipe.copy()
        names = [name for name, _ in recipe]
        addition = rcp.Add(names)
        recipe.append((name, addition))
        return recipe

    def generate_recipe_dataset(
        recipe: Union[Callable, List[Tuple[str, Callable]]],
        freq: str,
        start_date: pd.Timestamp,
        max_train_length: int,
        prediction_length: int,
        num_timeseries: int,
        trim_length_func: Callable = lambda x, **kwargs: 0,
    ) -> gluonts.dataset.common.TrainDatasets:
        """
        Generate GluonTS TrainDatasets from recipe.

        For more information on recipes, see
        https://gluon-ts.mxnet.io/_modules/gluonts/dataset/artificial/_base.html#RecipeDataset
        and
        https://gluon-ts.mxnet.io/examples/synthetic_data_generation_tutorial/tutorial.html.

        For `feat_dynamic_cat` and `feat_dynamic_real` generation pass in
        `shape=(n_features, 0)`. GluonTS replaces `0` in shape with
        `max_train_length + prediction_length`.

        :param recipe: GluonTS recipe. Datasets with keys `feat_dynamic_cat`,
            `feat_dynamic_real` and `target` are passed into `ListDataset`.
        :param freq: frequency
        :param start_date: start date of the dataset
        :param max_train_length: maximum length of a training time series
        :param prediction_length: length of prediction range
        :param num_timeseries: number of time series to generate
        :param trim_length_func: Callable f(x: int) -> int returning the
            (shortened) training length
        :return: GluonTS TrainDatasets (with `train` and `test` attributes).
        """
        names = [name for name, _ in recipe]
        dbg.dassert_in("target", names)
        metadata = gluonts.dataset.common.MetaData(freq=freq)
        recipe_dataset = gda.RecipeDataset(
            recipe,
            metadata,
            max_train_length,
            prediction_length,
            num_timeseries,
            trim_length_fun=trim_length_func,
            data_start=start_date,
        )
        return recipe_dataset.generate()


class ArmaProcess:
    """
    A thin wrapper around statsmodels `ArmaProcess`, with Pandas support.
    """

    def __init__(self, ar_coeffs: List[float], ma_coeffs: List[float]) -> None:
        """
        Initialize `arma_process` using given coefficients.

        Useful properties include
          - arroots
          - isinvertible
          - isstationary
          - maroots

        Further details are available at
          - https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima_process.ArmaProcess.html  # pylint: disable=line-too-long
        """
        self.ar_coeffs = ar_coeffs
        self.ma_coeffs = ma_coeffs
        self.arma_process = sm.tsa.ArmaProcess.from_coeffs(
            self.ar_coeffs, self.ma_coeffs
        )

    def generate_sample(
        self,
        date_range_kwargs: Dict[str, Any],
        scale: float = 1,
        burnin: float = 0,
        seed: Optional[int] = None,
    ) -> pd.Series:
        """
        Generate an ARMA realization.

        This wraps statsmodels' `generate_sample`, placing the values in a
        `pd.Series` with index specified through the date range parameters.

        :param date_range_kwargs: kwargs to forward to `pd.date_range`, e.g.,
          - "start", "end", "periods", "freq"
        :param scale: standard deviation of noise
        :param burnin: number of leading samples to drop
        :seed: np.random.seed seed
        """
        if seed is None:
            seed = 0
        np.random.seed(seed)
        # Create index and infer number of samples.
        index = pd.date_range(**date_range_kwargs)
        nsample = index.size
        # Generate the time series.
        data = self.arma_process.generate_sample(
            nsample=nsample, scale=scale, burnin=burnin
        )
        # Create series index and name.
        name = f"arma({len(self.ar_coeffs)},{len(self.ma_coeffs)})"
        return pd.Series(index=index, data=data, name=name)


class MultivariateNormalProcess:
    """
    A wrapper around sp.stats.multivariate_normal, with Pandas support.
    """

    def __init__(
        self,
        mean: Optional[pd.Series] = None,
        cov: Optional[pd.DataFrame] = None,
        allow_singular: Optional[bool] = None,
    ) -> None:
        """
        Optionally initialize mean and covariance of multivariate normal RV.
        """
        self.mean = self._maybe_return_values(mean, pd.Series)
        self.cov = self._maybe_return_values(cov, pd.DataFrame)
        self.allow_singular = allow_singular

    def set_cov_from_inv_wishart_draw(
        self, dim: int, seed: Optional[int] = None
    ) -> None:
        """
        Set covariance matrix equal to a draw from Inverse Wishart.

        - Defaults to least informative proper distribution
        - Takes dof = dim, scale = identify matrix of dimension `dim`

        https://docs.scipy.org/doc/scipy-0.16.0/reference/generated/scipy.stats.invwishart.html#scipy.stats.invwishart
        """
        scale = np.identity(dim)
        rv = sp.stats.invwishart(df=dim, scale=scale)
        self.cov = rv.rvs(random_state=seed)

    def generate_sample(
        self, date_range_kwargs: Dict[str, Any], seed: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Generate a multivariate normal distribution sample over index.

        https://docs.scipy.org/doc/scipy-0.16.0/reference/generated/scipy.stats.multivariate_normal.html#scipy.stats.multivariate_normal
        """
        index = pd.date_range(**date_range_kwargs)
        nsample = index.size
        rv = sp.stats.multivariate_normal(
            mean=self.mean, cov=self.cov, allow_singular=self.allow_singular
        )
        data = rv.rvs(size=nsample, random_state=seed)
        return pd.DataFrame(index=index, data=data)

    @staticmethod
    def _maybe_return_values(
        obj: Union[pd.Series, pd.DataFrame, None],
        expected_type: Union[pd.Series, pd.DataFrame],
    ) -> Union[None, np.array]:
        """
        Return values of series or dataframe or else None if object is None.

        This is a convenience method used in initialization.
        """
        if obj is None:
            return None
        if isinstance(obj, expected_type):
            return obj.values
        raise ValueError(f"Unsupported type {type(obj)}")


class PoissonProcess:
    """
    A thin wrapper around sp.stats.poisson, with Pandas support.
    """

    def __init__(self, mu: float) -> None:
        """
        Set shape parameter.
        """
        self.mu = mu

    def generate_sample(
        self, date_range_kwargs: Dict[str, Any], seed: Optional[int] = None
    ) -> pd.Series:
        """
        Generate a Poisson sample over index.

        https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.poisson.html
        """
        index = pd.date_range(**date_range_kwargs)
        nsample = index.size
        rv = sp.stats.poisson(
            mu=self.mu
        )
        data = rv.rvs(size=nsample, random_state=seed)
        return pd.Series(index=index, data=data, name="Poisson")


def generate_arima_signal_and_response(
    start_date: str,
    freq: str,
    num_periods: int,
    num_x_vars: int,
    base_random_state: int = 0,
    shift: int = 1,
) -> pd.DataFrame:
    """
    Generate dataframe of predictors and response.

    Example data:
                               x0        x1         y
    2010-01-01 00:00:00  0.027269  0.010088  0.014319
    2010-01-01 00:01:00  0.024221 -0.017519  0.034699
    2010-01-01 00:02:00  0.047438 -0.014653  0.036345
    2010-01-01 00:03:00  0.025131 -0.028136  0.024469
    2010-01-01 00:04:00  0.022443 -0.016625  0.025981

    :param start_date: index start date
    :param freq: index frequency
    :param num_periods: number of data points
    :param num_x_vars: number of predictors
    :param base_random_state: random state of this generator
    :param shift: shift `y` relatively to `x`
    :return:
    """
    np.random.seed(base_random_state)
    # Generate `x_vals`.
    x_vals = [
        _generate_arima_sample(
            random_state=base_random_state + i, n_periods=num_periods + shift
        )
        for i in range(num_x_vars)
    ]
    x_vals = np.vstack(x_vals).T
    # Generate `y` as linear combination of `x_i`.
    weights = np.random.dirichlet(np.ones(num_x_vars), 1).flatten()
    y = np.average(x_vals, axis=1, weights=weights)
    # Shift `y` (`y = weighted_sum(x).shift(shift)`).
    x = x_vals[shift:]
    y = y[:-shift]
    # Generate a dataframe.
    x_y = np.hstack([x, y.reshape(-1, 1)])
    idx = pd.date_range(start_date, periods=num_periods, freq=freq)
    x_cols = [f"x{i}" for i in range(num_x_vars)]
    return pd.DataFrame(x_y, index=idx, columns=x_cols + ["y"])


def _generate_arima_sample(
    random_state: int = 42,
    n_periods: int = 20,
    ar: Iterable[float] = np.array([0.462, -0.288]),
    ma: Iterable[float] = np.array([0.01]),
) -> np.array:
    np.random.seed(random_state)
    return sm.tsa.arma_generate_sample(ar=ar, ma=ma, nsample=n_periods, burnin=10)


def get_heaviside(a: int, b: int, zero_val: int, tick: int) -> pd.Series:
    """
    Generate Heaviside pd.Series.
    """
    dbg.dassert_lte(a, zero_val)
    dbg.dassert_lte(zero_val, b)
    array = np.arange(a, b, tick)
    srs = pd.Series(
        data=np.heaviside(array, zero_val), index=array, name="Heaviside"
    )
    return srs


def get_impulse(a: int, b: int, tick: int) -> pd.Series:
    """
    Generate unit impulse pd.Series.
    """
    heavi = get_heaviside(a, b, 1, tick)
    impulse = (heavi - heavi.shift(1)).shift(-1).fillna(0)
    impulse.name = "impulse"
    return impulse


def get_binomial_tree(
    p: Union[float, Iterable[float]],
    vol: float,
    size: Union[int, Tuple[int, ...], None],
    seed: Optional[int] = None,
) -> pd.Series:
    # binomial_tree(0.5, 0.1, 252, seed=0).plot()
    np.random.seed(seed=seed)
    pos = np.random.binomial(1, p, size)
    neg = np.full(size, 1) - pos
    delta = float(vol) * (pos - neg)
    return pd.Series(np.exp(delta.cumsum()), name="binomial_walk")


def get_gaussian_walk(
    drift: Union[float, Iterable[float]],
    vol: Union[float, Iterable[float]],
    size: Union[int, Tuple[int, ...], None],
    seed: Optional[int] = None,
) -> pd.Series:
    # get_gaussian_walk(0, .2, 252, seed=10)
    np.random.seed(seed=seed)
    gauss = np.random.normal(drift, vol, size)
    return pd.Series(np.exp(gauss.cumsum()), name="gaussian_walk")
