from core.generator.data import CodeType
import shortuuid


def get_new_code(code_type: CodeType) -> str:
    match code_type:
        case CodeType.UKZ:
            return get_ukz_code()
        case _:
            raise ValueError("Неподдерживаемый формат кода!")


def get_ukz_code() -> str:
    """
    Генерирует код УКЗ Беларуси
    :return:
    Возвращает строку код формата 019481043190000021255943532CAC
    """
    return shortuuid.ShortUUID().random(30)
