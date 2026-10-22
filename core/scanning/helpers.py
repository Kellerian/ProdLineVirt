from math import floor, ceil, sqrt
from random import randint
from typing import Iterator

STEP = 6 + 315
JITTER = 4


def get_grid(grid_size: int) -> tuple[int, int]:
    """
    Возвращает максимально квадратный размер сетки для размера

    :param grid_size: Количество ячеек в сетке
    :return: Возращает кортеж с количеством колонок и строк
    """
    cols = floor(sqrt(grid_size))
    rows = ceil(grid_size / cols)
    return cols, rows


def code_coord(cells: int, jitter: int = JITTER) -> Iterator[tuple[int, int]]:
    """
    Генерирует сетку по заданному размеру.
    К каждой точке добавляется случайный сдвиг, чтобы коды
    не получали одни и те же координаты.

    :param cells: Количество ячеек в сетке
    :param jitter: Максимальный сдвиг по каждой оси, пиксели
    :return: возвращает кортеж координат x, y
    """
    cols, rows = get_grid(cells)
    for h in range(cols):
        for w in range(rows):
            x = STEP * w + randint(-jitter, jitter)
            y = STEP * h + randint(-jitter, jitter)
            yield max(0, x), max(0, y)
