class Board:
    WIDTH = 10
    HEIGHT = 20

    def __init__(self):
        self.grid = [[0] * self.WIDTH for _ in range(self.HEIGHT)]

    def is_valid_position(self, piece_cells):
        for row, col in piece_cells:
            if col < 0 or col >= self.WIDTH:
                return False
            if row < 0 or row >= self.HEIGHT:
                return False
            if self.grid[row][col] != 0:
                return False
        return True

    def lock_piece(self, piece_cells, color):
        for row, col in piece_cells:
            if 0 <= row < self.HEIGHT and 0 <= col < self.WIDTH:
                self.grid[row][col] = color

    def clear_lines(self):
        cleared = 0
        new_grid = []
        for row in self.grid:
            if all(cell != 0 for cell in row):
                cleared += 1
            else:
                new_grid.append(row)
        for _ in range(cleared):
            new_grid.insert(0, [0] * self.WIDTH)
        self.grid = new_grid
        return cleared

    def is_game_over(self):
        return any(cell != 0 for cell in self.grid[0])
