"""
Tests for apps/ingest/producer.py.

load_dataset() tests hit the real XLSX on disk — no mocks needed.
main() tests mock KafkaProducer to avoid needing a live broker.
"""
import sys
import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import producer as prod

XLSX_PATH = str(
    Path(__file__).parent.parent.parent.parent / "data" / "raw_datasets" / "online_retail_II.xlsx"
)


# ---------------------------------------------------------------------------
# load_dataset()
# ---------------------------------------------------------------------------

class TestLoadDataset:

    def test_loads_without_error(self):
        rows = prod.load_dataset(XLSX_PATH)
        assert rows is not None

    def test_returns_non_empty_list(self):
        rows = prod.load_dataset(XLSX_PATH)
        assert isinstance(rows, list)
        assert len(rows) > 0

    def test_columns_are_snake_case(self):
        rows = prod.load_dataset(XLSX_PATH)
        row = rows[0]
        assert "invoice" in row
        assert "stock_code" in row
        assert "invoice_date" in row
        assert "customer_id" in row

    def test_original_excel_column_names_not_present(self):
        rows = prod.load_dataset(XLSX_PATH)
        row = rows[0]
        assert "Invoice" not in row
        assert "StockCode" not in row
        assert "InvoiceDate" not in row
        assert "Customer ID" not in row

    def test_invoice_date_is_string_not_datetime(self):
        rows = prod.load_dataset(XLSX_PATH)
        assert isinstance(rows[0]["invoice_date"], str)

    def test_invoice_date_is_iso_format(self):
        rows = prod.load_dataset(XLSX_PATH)
        date = rows[0]["invoice_date"]
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", date), f"Bad format: {date}"

    def test_rows_sorted_oldest_first(self):
        rows = prod.load_dataset(XLSX_PATH)
        dates = [r["invoice_date"] for r in rows[:1000]]
        assert dates == sorted(dates)

    def test_no_null_invoice_dates(self):
        rows = prod.load_dataset(XLSX_PATH)
        for row in rows:
            assert row["invoice_date"] is not None

    def test_customer_id_is_string_or_none(self):
        rows = prod.load_dataset(XLSX_PATH)
        for row in rows[:500]:
            assert row["customer_id"] is None or isinstance(row["customer_id"], str)


# ---------------------------------------------------------------------------
# main() — KafkaProducer mocked
# ---------------------------------------------------------------------------

class TestMain:

    def _mock_producer(self):
        m = MagicMock()
        m.send = MagicMock()
        m.flush = MagicMock()
        return m

    def test_exits_when_file_not_found(self):
        with patch.dict("os.environ", {"DATASET_PATH": "/does/not/exist.xlsx"}):
            with pytest.raises(SystemExit) as exc:
                prod.main()
        assert exc.value.code == 1

    def test_exits_when_broker_unreachable(self):
        from kafka.errors import NoBrokersAvailable
        with patch("producer.KafkaProducer", side_effect=NoBrokersAvailable):
            with patch.dict("os.environ", {"DATASET_PATH": XLSX_PATH}):
                with pytest.raises(SystemExit) as exc:
                    prod.main()
        assert exc.value.code == 1

    def test_send_called_once_per_row(self):
        mock = self._mock_producer()
        with patch("producer.KafkaProducer", return_value=mock):
            with patch("producer.time.sleep"):
                with patch.dict("os.environ", {"DATASET_PATH": XLSX_PATH}):
                    prod.main()
        expected_rows = len(prod.load_dataset(XLSX_PATH))
        assert mock.send.call_count == expected_rows

    def test_send_targets_correct_topic(self):
        mock = self._mock_producer()
        with patch("producer.KafkaProducer", return_value=mock):
            with patch("producer.time.sleep"):
                with patch.dict("os.environ", {"DATASET_PATH": XLSX_PATH}):
                    prod.main()
        for c in mock.send.call_args_list:
            assert c.args[0] == prod.TOPIC

    def test_message_value_is_json_serializable(self):
        mock = self._mock_producer()
        with patch("producer.KafkaProducer", return_value=mock):
            with patch("producer.time.sleep"):
                with patch.dict("os.environ", {"DATASET_PATH": XLSX_PATH}):
                    prod.main()
        value = mock.send.call_args_list[0].kwargs["value"]
        assert isinstance(value, dict)
        json.dumps(value)  # raises if not serializable

    def test_flush_called_at_least_once(self):
        mock = self._mock_producer()
        with patch("producer.KafkaProducer", return_value=mock):
            with patch("producer.time.sleep"):
                with patch.dict("os.environ", {"DATASET_PATH": XLSX_PATH}):
                    prod.main()
        assert mock.flush.call_count >= 1
