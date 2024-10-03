from random import randint


def extract_barcode_value_from_template(msg_received: str) -> list[str]:
    msg_rows = msg_received.split("\n")
    extracted_data: list[str] = []
    for r, row in enumerate(msg_rows):
        dm_extracted = ''
        if 'BARCODE=' in row:
            row = row.replace('BARCODE=', '')
            row = row.replace('~d034', '"')
            dm_extracted = row.strip()
        elif 'DMATRIX' in row or "BARCODE " in row:
            params = row.split('"')
            if 'DMATRIX' in row:
                splitted = params[1]
            else:
                splitted = params[-2]
            dm_extracted = splitted.replace('~d034', '"').strip()
        elif 'XRB' in row:
            r_n = msg_rows[r + 1]
            dm_extracted = r_n.strip()
        elif 'BR,24,24' in row:
            row = row.replace('BR,24,24,2,5,250,0,1,', '')
            row = row.replace('~d034', '"')
            dm_extracted = row.strip()
        elif '^FH^FD_7e' in row:
            row = row.replace('^FH^FD_7e', '')
            row = row.replace('^FS', '')
            dm_extracted = row.strip()
        if dm_extracted and len(dm_extracted) >= 13:
            extracted_data.append(dm_extracted)
    return extracted_data


def process_barcode(barcode: str) -> str:
    if barcode.startswith("~1"):
        barcode = barcode[2:]
    if '07808631857726' in barcode:
        weight = randint(100, 1000)
        barcode = (
            f"{barcode}{chr(29)}3103{weight:06}"
        )
    return barcode
