"""
xlsx2csv-mergefill: Excel→CSV with merged-cell fill (cp932)

Public API for xlsx2csv-mergefill package.
"""

from .core import (
    convert_file,
    read_sheet,
    read_workbook,
    list_sheets,
    to_csv_string,
    # deprecated aliases
    excel_to_csv,
    load_excel_data,
    load_all_sheets_data,
    get_sheet_names,
    data_to_csv_string,
)

__all__ = [
    "convert_file",
    "read_sheet",
    "read_workbook",
    "list_sheets",
    "to_csv_string",
    # deprecated aliases
    "excel_to_csv",
    "load_excel_data",
    "load_all_sheets_data",
    "get_sheet_names",
    "data_to_csv_string",
]
