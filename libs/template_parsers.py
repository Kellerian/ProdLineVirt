from random import randint


def extract_barcode_value_from_template(msg_received: str) -> list[str]:
    msg_rows = msg_received.split("\n")
    extracted_data: list[str] = []
    for r, t_row in enumerate(msg_rows, start=0):
        row = t_row.strip()
        dm_extracted = ''
        if row.startswith('BARCODE='):
            row = row.replace('BARCODE=', '')
            row = row.replace('~d034', '"')
            dm_extracted = row.strip()
        elif row.startswith('DMATRIX') or row.startswith("BARCODE "):
            params = row.split('"')
            if 'DMATRIX' in row:
                splitted = params[1]
            else:
                splitted = params[-2]
            dm_extracted = splitted.replace('~d034', '"').strip()
        elif row.startswith('XRB'):
            r_n = msg_rows[r + 1]
            dm_extracted = r_n.strip()
        elif row.startswith('BR,'):
            row = row.replace('BR,24,24,2,5,250,0,1,', '')
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


if __name__ == '__main__':
    template = """
    
    
    ^Q15,2
^W15
^H15
^R40
^L
AT,0,120,32,32,0,0,0,0,{ai21}
XRB21,15,6,0,35
aolih489au894auj894atu0ajr
E
    """
    print(extract_barcode_value_from_template(template))
