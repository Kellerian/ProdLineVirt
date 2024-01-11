import psycopg
from psycopg.rows import dict_row


def get_chw_codes(order_id: int, ip: str, port: int, dbname: str) -> list[str]:
    with psycopg.connect(
        f"postgresql://postgres:postgres@{ip}:{port}/{dbname}",
        row_factory=dict_row
    ) as conn:
        q_text = "SELECT gtin, serial, cripto93 FROM scripto WHERE orderid=%s"
        with conn.cursor() as cur:
            cur.execute(q_text, [order_id])
            return [
                f"01{row['gtin']}21{row['serial']}{chr(29)}93{row['cripto93']}"
                for row in cur
            ]
