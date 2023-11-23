from enum import Enum


class CodeQuality(Enum):
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    E = 'E'
    F = 'F'


GOOD_CODES = (CodeQuality.A.value, CodeQuality.B.value)


BAD_CODES = (
    CodeQuality.C.value,
    CodeQuality.D.value,
    CodeQuality.E.value,
    CodeQuality.F.value
)
