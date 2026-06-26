from io import BytesIO
from pathlib import Path

import pandas as pd


SUPPORTED_EXTENSIONS = {
    ".csv",
    ".xls",
    ".xlsx",
    ".xlsm"
}


COLUMN_ALIASES = {
    "date": [
        "date",
        "timestamp",
        "time",
        "tradingdate",
        "datetime"
    ],
    "open": [
        "open",
        "openprice"
    ],
    "high": [
        "high",
        "highprice"
    ],
    "low": [
        "low",
        "lowprice"
    ],
    "close": [
        "close",
        "closingprice",
        "ltp",
        "lastprice"
    ],
    "volume": [
        "volume",
        "vol",
        "qty",
        "quantity",
        "shares"
    ]
}


def load_market_file(
    file_bytes: bytes,
    filename: str
) -> pd.DataFrame:

    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    if extension == ".csv":
        return pd.read_csv(
            BytesIO(file_bytes)
        )

    return pd.read_excel(
        BytesIO(file_bytes)
    )


def normalize_dataframe(
    df: pd.DataFrame
) -> pd.DataFrame:

    frame = df.copy()

    frame.columns = [
        str(col).strip().lower().replace(" ", "")
        for col in frame.columns
    ]

    return frame


def identify_columns(
    df: pd.DataFrame
) -> dict:

    mapping = {}

    for target, aliases in COLUMN_ALIASES.items():

        found = None

        for column in df.columns:

            normalized = (
                str(column)
                .lower()
                .replace(" ", "")
            )

            if normalized in aliases:
                found = column
                break

        if found is None:
            raise ValueError(
                f"Required column missing: {target}"
            )

        mapping[target] = found

    return mapping


def parse_dates(
    series: pd.Series
) -> pd.Series:

    return pd.to_datetime(
        series,
        errors="coerce"
    )


def clean_numeric(
    series: pd.Series
) -> pd.Series:

    return pd.to_numeric(
        series,
        errors="coerce"
    )


def prepare_market_dataframe(
    file_bytes: bytes,
    filename: str
):

    df = load_market_file(
        file_bytes,
        filename
    )

    df = normalize_dataframe(df)

    columns = identify_columns(df)

    df["date"] = parse_dates(
        df[columns["date"]]
    )

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    for col in numeric_columns:

        source_col = columns[col]

        df[col] = clean_numeric(
            df[source_col]
        )

    df = df.dropna(
        subset=[
            "date",
            "open",
            "high",
            "low",
            "close"
        ]
    )

    df = df.sort_values(
        by="date"
    )

    df = df.reset_index(
        drop=True
    )

    return df