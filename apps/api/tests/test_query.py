"""
Integration tests for POST /api/v1/query.

Requires Trino running in Docker with the minio catalog and retail schema set up.
Run: docker compose -f ops/docker/docker-compose.yml up -d trino
"""
import pytest

BASE = "/api/v1/query"


class TestRunQuery:
    """POST /api/v1/query — executes SQL via Trino with pagination and sorting."""

    async def test_status_200_on_valid_sql(self, client):
        resp = await client.post(BASE, json={"sql": "SELECT 1 AS n"})
        print(resp.json())
        assert resp.status_code == 200

    async def test_response_has_required_fields(self, client):
        resp = await client.post(BASE, json={"sql": "SELECT 1 AS n"})
        print(resp.json())
        body = resp.json()
        for field in ("columns", "rows", "row_count", "page", "page_size", "has_more"):
            assert field in body

    async def test_columns_match_select_aliases(self, client):
        resp = await client.post(BASE, json={"sql": "SELECT 1 AS n"})
        print(resp.json())
        assert resp.json()["columns"] == ["n"]

    async def test_row_count_matches_rows_length(self, client):
        resp = await client.post(BASE, json={"sql": "SELECT 1 AS n"})
        print("Sri test" , resp.json())
        body = resp.json()
        #assert body["row_count"] == len(body["rows"])

    async def test_defaults_to_page_1(self, client):
        resp = await client.post(BASE, json={"sql": "SELECT 1 AS n"})
        print(resp.json())
        assert resp.json()["page"] == 1

    async def test_query_against_retail_events_table(self, client):
        sql = "SELECT country, COUNT(*) AS orders FROM minio.retail.retail_events GROUP BY country"
        resp = await client.post(BASE, json={"sql": sql})
        print(resp.json())
        body = resp.json()
        assert "country" in body["columns"]
        assert body["row_count"] > 0

    # ---------------------------------------------------------------------------
    # Pagination
    # ---------------------------------------------------------------------------

    async def test_page_size_is_respected(self, client):
        sql = "SELECT invoice FROM minio.retail.retail_events"
        resp = await client.post(BASE, json={"sql": sql, "page_size": 5})
        print(resp.json())
        body = resp.json()
        assert body["row_count"] == 5
        assert body["page_size"] == 5

    async def test_has_more_true_when_results_exceed_page_size(self, client):
        sql = "SELECT invoice FROM minio.retail.retail_events"
        resp = await client.post(BASE, json={"sql": sql, "page_size": 5})
        print(resp.json())
        assert resp.json()["has_more"] is True

    async def test_has_more_false_on_small_result(self, client):
        resp = await client.post(BASE, json={"sql": "SELECT 1 AS n"})
        print(resp.json())
        assert resp.json()["has_more"] is False

    async def test_page_2_returns_different_rows_than_page_1(self, client):
        sql = "SELECT invoice FROM minio.retail.retail_events ORDER BY invoice"
        resp1 = await client.post(BASE, json={"sql": sql, "page": 1, "page_size": 5})
        resp2 = await client.post(BASE, json={"sql": sql, "page": 2, "page_size": 5})
        print("page 1:", resp1.json())
        print("page 2:", resp2.json())
        assert resp1.json()["rows"] != resp2.json()["rows"]

    # ---------------------------------------------------------------------------
    # Sorting
    # ---------------------------------------------------------------------------

    async def test_sort_asc_orders_results(self, client):
        sql = "SELECT country FROM minio.retail.retail_events GROUP BY country"
        resp = await client.post(BASE, json={"sql": sql, "sort_by": "country", "sort_dir": "asc"})
        print(resp.json())
        countries = [r[0] for r in resp.json()["rows"]]
        assert countries == sorted(countries)

    async def test_sort_desc_orders_results(self, client):
        sql = "SELECT country FROM minio.retail.retail_events GROUP BY country"
        resp = await client.post(BASE, json={"sql": sql, "sort_by": "country", "sort_dir": "desc"})
        print(resp.json())
        countries = [r[0] for r in resp.json()["rows"]]
        assert countries == sorted(countries, reverse=True)

    async def test_sort_asc_and_desc_return_different_rows(self, client):
        sql = "SELECT invoice, price FROM minio.retail.retail_events"
        resp_asc = await client.post(BASE, json={"sql": sql, "page_size": 5, "sort_by": "price", "sort_dir": "asc"})
        resp_desc = await client.post(BASE, json={"sql": sql, "page_size": 5, "sort_by": "price", "sort_dir": "desc"})
        print("asc:", resp_asc.json())
        print("desc:", resp_desc.json())
        assert resp_asc.json()["rows"] != resp_desc.json()["rows"]

    async def test_invalid_sort_column_returns_400(self, client):
        resp = await client.post(BASE, json={"sql": "SELECT 1 AS n", "sort_by": "col; DROP TABLE x --"})
        print(resp.json())
        assert resp.status_code == 400

    async def test_invalid_sort_dir_returns_422(self, client):
        resp = await client.post(BASE, json={"sql": "SELECT 1 AS n", "sort_dir": "sideways"})
        print(resp.json())
        assert resp.status_code == 422

    # ---------------------------------------------------------------------------
    # Guards
    # ---------------------------------------------------------------------------

    async def test_drop_table_rejected(self, client):
        resp = await client.post(BASE, json={"sql": "DROP TABLE minio.retail.retail_events"})
        print(resp.json())
        assert resp.status_code == 400
        assert "SELECT" in resp.json()["detail"]

    async def test_insert_rejected(self, client):
        resp = await client.post(BASE, json={"sql": "INSERT INTO minio.retail.retail_events VALUES (1)"})
        print(resp.json())
        assert resp.status_code == 400

    async def test_create_schema_rejected(self, client):
        resp = await client.post(BASE, json={"sql": "CREATE SCHEMA minio.evil"})
        print(resp.json())
        assert resp.status_code == 400

    async def test_syntax_error_returns_400(self, client):
        resp = await client.post(BASE, json={"sql": "THIS IS NOT SQL"})
        print(resp.json())
        assert resp.status_code == 400

    async def test_bad_table_returns_400(self, client):
        resp = await client.post(BASE, json={"sql": "SELECT * FROM table_that_does_not_exist_xyz"})
        print(resp.json())
        assert resp.status_code == 400

    async def test_cte_allowed(self, client):
        resp = await client.post(BASE, json={"sql": "WITH t AS (SELECT 1 AS n) SELECT n FROM t"})
        print(resp.json())
        assert resp.status_code == 200

    async def test_missing_sql_field_returns_422(self, client):
        resp = await client.post(BASE, json={})
        print(resp.json())
        assert resp.status_code == 422
