from core.generator.data import CodeType
from random import randint
from libs.data import GS
import shortuuid


def get_new_code(gtin: str, code_type: CodeType) -> str:
    ai01 = f"01{gtin}"
    match code_type:
        case CodeType.UKZ:
            return ai01 + get_ai(21, 12)
        case CodeType.KM_01_14_21_6_93_4:
            return ai01 + get_ai(21, 6) + get_ai(93, 4)
        case CodeType.KM_01_14_21_6_93_4_3103_6:
            r_weight = randint(100, 999)
            ai3103 = f"{r_weight:>06}"
            return ai01 + get_ai(21, 6) + GS + get_ai(93, 4) + GS + ai3103
        case CodeType.KM_01_14_21_7_93_4:
            return ai01 + get_ai(21, 7) + GS + get_ai(93, 4)
        case CodeType.KM_01_14_21_13_93_4:
            return ai01 + get_ai(21, 13) + GS + get_ai(93, 4)
        case CodeType.KM_01_14_21_20_93_4:
            return ai01 + get_ai(21, 20) + GS + get_ai(93, 4)
        case CodeType.KM_01_14_21_6_91_4_92_44:
            return (
                ai01 + get_ai(21, 6) + GS + get_ai(91, 4) + GS + get_ai(92, 44)
            )
        case CodeType.KM_01_14_21_13_91_4_92_44:
            return (
                ai01 + get_ai(21, 13) + GS + get_ai(91, 4) + GS + get_ai(92, 44)
            )
        case CodeType.KM_01_14_21_20_91_4_92_44:
            return (
                ai01 + get_ai(21, 20) + GS + get_ai(91, 4) + GS + get_ai(92, 44)
            )
        case _:
            raise ValueError("Неподдерживаемый формат кода!")


def get_ai(ai: int, amount: int) -> str:
    ai_val = shortuuid.ShortUUID().random(amount)
    return f"{ai}{ai_val}"
