import io
import logging
import os

import pandas as pd

import core.dataflow.nodes.sinks as cdtfnosin
import helpers.unit_test as huntes

_LOG = logging.getLogger(__name__)


class TestWriteDf(huntes.TestCase):
    def test_write(self) -> None:
        """
        Round-trip test on df serializing/deserializing.
        """
        dir_name = self.get_scratch_space()
        df_writer = cdtfnosin.WriteDf("df_writer", dir_name)
        df = self._get_data()
        df_writer.predict(df)["df_out"]
        file_name = os.path.join(dir_name, "24199772.pq")
        reconstructed_df = pd.read_parquet(file_name)
        self.assert_dfs_close(reconstructed_df, df)

    def test_pass_through_no_writing(self) -> None:
        """
        Ensure that `df` is passed through when no `dir_name` is provided.
        """
        df_writer = cdtfnosin.WriteDf("df_writer", "")
        df = self._get_data()
        df_out = df_writer.predict(df)["df_out"]
        self.assert_dfs_close(df_out, df)

    def test_pass_through(self) -> None:
        """
        Ensure that `df` is passed through when `dir_name` is provided.
        """
        dir_name = self.get_scratch_space()
        df_writer = cdtfnosin.WriteDf("df_writer", dir_name)
        df = self._get_data()
        df_out = df_writer.predict(df)["df_out"]
        self.assert_dfs_close(df_out, df)

    @staticmethod
    def _get_data() -> pd.DataFrame:
        txt = """
,close,close,mid,mid
datetime,MN0,MN1,MN0,MN1
2016-01-04 16:00:00,95.00,96.00,100,98.00
2016-01-04 16:01:00,NaN,NaN,NaN,NaN
2016-01-05 09:29:00,NaN,NaN,NaN,NaN
2016-01-05 09:30:00,100.00,NaN,100,NaN
2016-01-05 09:31:00,105.00,98.00,106.05,97.02
2016-01-05 09:32:00,52.50,49.00,53.025,48.51
"""
        df = pd.read_csv(
            io.StringIO(txt), index_col=0, parse_dates=True, header=[0, 1]
        )
        return df


class TestWriteCols(huntes.TestCase):
    def test_write(self) -> None:
        dir_name = self.get_scratch_space()
        mapping = {"close": "price"}
        df_writer = cdtfnosin.WriteCols("df_writer", dir_name, mapping)
        df = self._get_data()
        df_writer.predict(df)["df_out"]
        file_name = os.path.join(dir_name, "24199772_price.csv")
        reconstructed_col = pd.read_csv(file_name, index_col=0)
        col = df.iloc[-1]["close"].rename("24199772_price").to_frame()
        self.assert_dfs_close(reconstructed_col, col)

    def test_pass_through_no_writing(self) -> None:
        df_writer = cdtfnosin.WriteCols("df_writer", "", {})
        df = self._get_data()
        df_out = df_writer.predict(df)["df_out"]
        self.assert_dfs_close(df_out, df)

    def test_pass_through(self) -> None:
        dir_name = self.get_scratch_space()
        col_mapping = {"mid": "mid_price"}
        df_writer = cdtfnosin.WriteCols("df_writer", dir_name, col_mapping)
        df = self._get_data()
        df_out = df_writer.predict(df)["df_out"]
        self.assert_dfs_close(df_out, df)

    @staticmethod
    def _get_data() -> pd.DataFrame:
        txt = """
,close,close,mid,mid
datetime,MN0,MN1,MN0,MN1
2016-01-04 16:00:00,95.00,96.00,100,98.00
2016-01-04 16:01:00,NaN,NaN,NaN,NaN
2016-01-05 09:29:00,NaN,NaN,NaN,NaN
2016-01-05 09:30:00,100.00,NaN,100,NaN
2016-01-05 09:31:00,105.00,98.00,106.05,97.02
2016-01-05 09:32:00,52.50,49.00,53.025,48.51
"""
        df = pd.read_csv(
            io.StringIO(txt), index_col=0, parse_dates=True, header=[0, 1]
        )
        return df