import abc
from typing import Optional

import pandas as pd

import instrument_master.common.data.types as vcdtyp


# TODO(*): Rename file abstract_data_extractor.py
class AbstractDataExtractor(abc.ABC):
    """
    Extract data from external sources (e.g., from IB TWS) and save / return
    it.
    """

    @abc.abstractmethod
    def extract_data(
        self,
        exchange: str,
        symbol: str,
        asset_class: vcdtyp.AssetClass,
        frequency: vcdtyp.Frequency,
        # TODO(*): contract_type should come before frequency, since it identifies
        #  the Symbol.
        contract_type: Optional[vcdtyp.ContractType] = None,
        start_ts: Optional[pd.Timestamp] = None,
        end_ts: Optional[pd.Timestamp] = None,
        incremental: Optional[bool] = None,
        dst_dir: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Extract the data for symbol, save it, and return it.

        :param exchange: name of the exchange
        :param symbol: symbol to get the data for
        :param asset_class: asset class
        :param frequency: `D` or `T` for daily or minutely data respectively
        :param contract_type: required for asset class of type `futures`
        :param start_ts: start timestamp of data to extract
            - `None`: the oldest available
        :param end_ts: end timestamp of data to extract
            - `None`: current time
        :param incremental: if True, save only the new data, if False remove the old
            data first and start from scratch
        :param dst_dir: path to store the data
        :return: a dataframe with the data
        """