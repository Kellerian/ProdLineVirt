"""Обратносовместимые обёртки извлечения кодов из шаблонов печати."""

if __name__ == "__main__" and __package__ is None:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.printing.extract import (
    extract_barcode_value_from_template,
    process_barcode,
)

__all__ = [
    "extract_barcode_value_from_template",
    "process_barcode",
]


if __name__ == "__main__":
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
