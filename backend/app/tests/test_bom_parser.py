from pathlib import Path

import pytest
from openpyxl import Workbook

from app.services.bom_parser import BomParserError, parse_bom_file


def test_parse_csv_bom(tmp_path: Path) -> None:
    path = tmp_path / "bom.csv"
    path.write_text(
        "Part Number,Description,Parent Assembly,Child Assembly,Revision\n"
        "P-100,Motor bracket,A-10,C-20,Rev A\n",
        encoding="utf-8",
    )

    result = parse_bom_file(path)

    assert len(result.rows) == 1
    assert result.rows[0].part_number == "P-100"
    assert result.rows[0].description == "Motor bracket"
    assert result.rows[0].parent_assembly == "A-10"
    assert result.rows[0].child_assembly == "C-20"
    assert result.rows[0].revision == "Rev A"


def test_parse_xlsx_bom(tmp_path: Path) -> None:
    path = tmp_path / "bom.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["part_no", "desc", "parent", "child", "rev"])
    sheet.append(["P-200", "Cooling tube", "A-11", "C-21", "B"])
    workbook.save(path)

    result = parse_bom_file(path)

    assert len(result.rows) == 1
    assert result.rows[0].part_number == "P-200"
    assert result.rows[0].description == "Cooling tube"
    assert result.rows[0].parent_assembly == "A-11"
    assert result.rows[0].child_assembly == "C-21"
    assert result.rows[0].revision == "B"


def test_parser_accepts_column_aliases(tmp_path: Path) -> None:
    path = tmp_path / "aliases.csv"
    path.write_text(
        "Item No,Item Description,Assembly,Component,Version\n"
        "P-300,Valve seal,A-12,C-22,C\n",
        encoding="utf-8",
    )

    result = parse_bom_file(path)

    assert result.rows[0].part_number == "P-300"
    assert result.rows[0].description == "Valve seal"
    assert result.rows[0].parent_assembly == "A-12"
    assert result.rows[0].child_assembly == "C-22"
    assert result.rows[0].revision == "C"


def test_missing_part_number_column_raises_error(tmp_path: Path) -> None:
    path = tmp_path / "missing.csv"
    path.write_text("Description,Revision\nMotor bracket,A\n", encoding="utf-8")

    with pytest.raises(BomParserError, match="missing required columns"):
        parse_bom_file(path)


def test_unsupported_extension_raises_error(tmp_path: Path) -> None:
    path = tmp_path / "bom.pdf"
    path.write_text("not parsed", encoding="utf-8")

    with pytest.raises(BomParserError, match="Only CSV and XLSX"):
        parse_bom_file(path)
