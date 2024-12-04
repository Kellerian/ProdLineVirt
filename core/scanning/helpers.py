from math import floor, ceil, sqrt
from typing import Iterator


def get_grid(grid_size: int) -> tuple[int, int]:
    """
    Возвращает максимально квадратный размер сетки для размера

    :param grid_size: Количество ячеек в сетке
    :return: Возращает кортеж с количеством колонок и строк
    """
    cols = floor(sqrt(grid_size))
    rows = ceil(grid_size / cols)
    return cols, rows


def code_coord(cells: int) -> Iterator[tuple[int, int]]:
    """
    Генерирует сетку по заданному размеру

    :param cells: Количество ячеек в сетке
    :return: возвращает кортеж координат x, y
    """
    cols, rows = get_grid(cells)
    for h in range(cols):
        for w in range(rows):
            x = (2 + 15) * w
            y = (2 + 15) * h
            yield x, y
