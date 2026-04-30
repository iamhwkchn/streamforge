import time
import trino
import psycopg2
from pathlib import Path

TRINO_HOST = "localhost"
TRINO_PORT = 8081
TRINO_USER = "admin"

POSTGRES_DSN = "host=localhost port=5432 dbname=streamforge user=admin password=password"

INIT_SQL = (Path(__file__).parent.parent / "ops" / "trino" / "init.sql").read_text()

FEATURE_SQL_TABLE = "retail_events"
FEATURE_SQL_TABLE_QUALIFIED = "minio.retail.retail_events"

VALIDATION_QUERIES = [
    (
        "Row count",
        "SELECT count(*) FROM minio.retail.retail_events",
    ),
    (
        "revenue_by_country (top 5)",
        "SELECT country, ROUND(SUM(price * quantity), 2) AS total_revenue"
        " FROM minio.retail.retail_events"
        " GROUP BY country ORDER BY total_revenue DESC LIMIT 5",
    ),
    (
        "top_customers_spend (top 5)",
        "SELECT customer_id, ROUND(SUM(price * quantity), 2) AS total_spend"
        " FROM minio.retail.retail_events"
        " WHERE customer_id IS NOT NULL"
        " GROUP BY customer_id ORDER BY total_spend DESC LIMIT 5",
    ),
    (
        "daily_order_volume (first 5 days)",
        "SELECT date_trunc('day', invoice_date) AS day,"
        " count(DISTINCT invoice) AS order_count"
        " FROM minio.retail.retail_events"
        " GROUP BY 1 ORDER BY 1 ASC LIMIT 5",
    ),
]


def wait_for_trino(host: str, port: int, retries: int = 15, delay: int = 5) -> bool:
    import urllib.request
    url = f"http://{host}:{port}/v1/info"
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                if resp.status == 200:
                    print("Trino is ready.")
                    return True
        except Exception:
            pass
        print(f"  Waiting for Trino... ({i + 1}/{retries})")
        time.sleep(delay)
    return False


def run_ddl(conn: trino.dbapi.Connection) -> None:
    # Split on semicolons, skip blanks, run each statement individually
    statements = [s.strip() for s in INIT_SQL.split(";") if s.strip()]
    cursor = conn.cursor()
    for stmt in statements:
        print(f"Running: {stmt[:80].replace(chr(10), ' ')}...")
        cursor.execute(stmt)
        # Fetch to drive execution (Trino is lazy)
        try:
            cursor.fetchall()
        except Exception:
            pass
    print("DDL complete.")


def update_feature_sql_in_postgres() -> None:
    print("Updating feature SQL in Postgres to use qualified table name...")
    with psycopg2.connect(POSTGRES_DSN) as pg:
        with pg.cursor() as cur:
            cur.execute(
                "UPDATE features SET sql_definition = REPLACE(sql_definition, %s, %s)"
                " WHERE sql_definition LIKE %s",
                (FEATURE_SQL_TABLE, FEATURE_SQL_TABLE_QUALIFIED, f"%{FEATURE_SQL_TABLE}%"),
            )
            print(f"  Updated {cur.rowcount} feature row(s).")
        pg.commit()


def validate(conn: trino.dbapi.Connection) -> None:
    print("\n--- Validation ---")
    cursor = conn.cursor()
    for label, sql in VALIDATION_QUERIES:
        print(f"\n[{label}]")
        cursor.execute(sql)
        rows = cursor.fetchall()
        for row in rows:
            print(" ", row)


def main() -> None:
    if not wait_for_trino(TRINO_HOST, TRINO_PORT):
        print("Trino did not become ready in time. Aborting.")
        return

    conn = trino.dbapi.connect(
        host=TRINO_HOST,
        port=TRINO_PORT,
        user=TRINO_USER,
        http_scheme="http",
    )

    run_ddl(conn)
    update_feature_sql_in_postgres()
    validate(conn)

    print("\nTrino init complete.")


if __name__ == "__main__":
    main()
