import os
from sqlalchemy import create_engine, text


def _get_engine():
    connection_string = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/market_intel",
    )
    return create_engine(connection_string, echo=False)


def _list_schemas(conn):
    result = conn.execute(
        text(
            """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name IN ('market_intel', 'public')
            """
        )
    )
    return [row[0] for row in result.fetchall()]


def _table_exists(conn, schema, table_name):
    result = conn.execute(
        text(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = :schema
              AND table_name = :table
            """
        ),
        {"schema": schema, "table": table_name},
    )
    return result.fetchone() is not None


def _existing_target_schemas(conn):
    schemas = _list_schemas(conn)
    targets = []
    for schema in schemas:
        if _table_exists(conn, schema, "filings"):
            targets.append(schema)
    return targets


def _delete_duplicates(conn, schema):
    conn.execute(text(f"SET search_path TO {schema}, public"))

    duplicates_cte = f"""
        WITH ranked AS (
            SELECT
                doc_id,
                ROW_NUMBER() OVER (
                    PARTITION BY announcement_id, company_code
                    ORDER BY created_at DESC, doc_id DESC
                ) AS rn
            FROM {schema}.filings
            WHERE announcement_id IS NOT NULL
        )
        SELECT doc_id FROM ranked WHERE rn > 1
    """

    dup_doc_ids = [row[0] for row in conn.execute(text(duplicates_cte)).fetchall()]
    if not dup_doc_ids:
        print(f"[{schema}] No duplicates found.")
        return

    print(f"[{schema}] Found {len(dup_doc_ids)} duplicate filings. Deleting...")

    dependent_tables = [
        "parsed_fields",
        "parsed_tables",
        "document_chunks",
        "shareholding_chunks",
        "financial_chunks",
        "dividend_chunks",
        "corporate_action_chunks",
        "meeting_chunks",
        "shareholding_changes",
        "financial_results",
    ]

    for table in dependent_tables:
        if _table_exists(conn, schema, table):
            conn.execute(
                text(f"DELETE FROM {schema}.{table} WHERE doc_id = ANY(:doc_ids)"),
                {"doc_ids": dup_doc_ids},
            )

    conn.execute(
        text(f"DELETE FROM {schema}.filings WHERE doc_id = ANY(:doc_ids)"),
        {"doc_ids": dup_doc_ids},
    )

    print(f"[{schema}] Deleted duplicates.")


def _add_unique_index(conn, schema):
    conn.execute(text(f"SET search_path TO {schema}, public"))
    index_name = "uq_filings_announcement_company"
    conn.execute(
        text(
            f"""
            CREATE UNIQUE INDEX IF NOT EXISTS {index_name}
            ON {schema}.filings (announcement_id, company_code)
            WHERE announcement_id IS NOT NULL
            """
        )
    )
    print(f"[{schema}] Ensured unique index {index_name}.")


def main():
    engine = _get_engine()
    with engine.begin() as conn:
        schemas = _existing_target_schemas(conn)
        if not schemas:
            print("No filings table found in target schemas.")
            return

        for schema in schemas:
            _delete_duplicates(conn, schema)
            _add_unique_index(conn, schema)


if __name__ == "__main__":
    main()
