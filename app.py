from flask import Flask, render_template, request, jsonify
import json
import time
from collections import defaultdict
import copy

app = Flask(__name__)

class SudokuVisualizer:
    def __init__(self):
        self.size = 9
        self.grid = [[0 for _ in range(9)] for _ in range(9)]
        self.graph = defaultdict(set)
        self.cell_positions = {}
        self.steps = []  # Lưu các bước giải
        
    def set_grid(self, grid):
        """Thiết lập lưới Sudoku"""
        self.grid = [row[:] for row in grid]
        self.build_constraint_graph()
        self.steps = []
        
    def build_constraint_graph(self):
        """Xây dựng đồ thị ràng buộc cho Sudoku"""
        self.graph = defaultdict(set)
        self.cell_positions = {}
        
        # Tạo mapping từ cell index đến vị trí
        cell_index = 0
        for i in range(9):
            for j in range(9):
                self.cell_positions[cell_index] = (i, j)
                cell_index += 1
        
        # Tạo cạnh giữa các ô có ràng buộc
        for cell1 in range(81):
            row1, col1 = self.cell_positions[cell1]
            
            for cell2 in range(cell1 + 1, 81):
                row2, col2 = self.cell_positions[cell2]
                
                # Kiểm tra ràng buộc
                if (row1 == row2 or  # Cùng hàng
                    col1 == col2 or  # Cùng cột
                    (row1 // 3 == row2 // 3 and col1 // 3 == col2 // 3)):  # Cùng ô 3x3
                    self.graph[cell1].add(cell2)
                    self.graph[cell2].add(cell1)
    
    def validate_input(self, grid):
        """Kiểm tra tính hợp lệ của input và trả về conflicts"""
        conflicts = []
        
        for i in range(9):
            for j in range(9):
                if grid[i][j] != 0:
                    # Tạm thời xóa giá trị để kiểm tra
                    temp = grid[i][j]
                    grid[i][j] = 0
                    
                    if not self.is_valid_placement(grid, i, j, temp):
                        conflicts.append((i, j))
                    
                    grid[i][j] = temp
        
        return conflicts
    
    def is_valid_placement(self, grid, row, col, num):
        """Kiểm tra xem có thể đặt số num vào vị trí (row, col) không"""
        # Kiểm tra hàng
        for c in range(9):
            if grid[row][c] == num:
                return False
        
        # Kiểm tra cột
        for r in range(9):
            if grid[r][col] == num:
                return False
        
        # Kiểm tra ô 3x3
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for r in range(start_row, start_row + 3):
            for c in range(start_col, start_col + 3):
                if grid[r][c] == num:
                    return False
        
        return True
    
    def get_possible_values(self, grid, row, col):
        """Lấy các giá trị có thể điền vào ô (row, col)"""
        if grid[row][col] != 0:
            return [grid[row][col]]
        
        possible = []
        for num in range(1, 10):
            if self.is_valid_placement(grid, row, col, num):
                possible.append(num)
        
        return possible
    
    def get_conflicts_for_cell(self, grid, row, col):
        """Lấy danh sách các ô xung đột với ô (row, col)"""
        conflicts = []
        current_value = grid[row][col]
        
        if current_value == 0:
            return conflicts
        
        # Kiểm tra hàng
        for c in range(9):
            if c != col and grid[row][c] == current_value:
                conflicts.append((row, c))
        
        # Kiểm tra cột
        for r in range(9):
            if r != row and grid[r][col] == current_value:
                conflicts.append((r, col))
        
        # Kiểm tra ô 3x3
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for r in range(start_row, start_row + 3):
            for c in range(start_col, start_col + 3):
                if (r, c) != (row, col) and grid[r][c] == current_value:
                    conflicts.append((r, c))
        
        return conflicts
    
    def solve_step_by_step(self):
        """Giải Sudoku từng bước với visualization"""
        solution = [row[:] for row in self.grid]
        original_grid = [row[:] for row in self.grid]
        self.steps = []
        
        # Bước 1: Hiển thị trạng thái ban đầu
        self.steps.append({
            'step_number': 0,
            'description': 'Trạng thái ban đầu - Xây dựng đồ thị ràng buộc',
            'grid': [row[:] for row in solution],
            'current_cell': None,
            'possible_values': {},
            'action': 'initialize',
            'conflicts': self.validate_input(solution)
        })
        
        def get_empty_cells_with_constraints():
            """Lấy danh sách ô trống với thông tin ràng buộc"""
            empty_cells = []
            for i in range(9):
                for j in range(9):
                    if solution[i][j] == 0:
                        possible = self.get_possible_values(solution, i, j)
                        empty_cells.append((i, j, len(possible), possible))
            
            # Sắp xếp theo MRV (Most Restrictive Variable)
            empty_cells.sort(key=lambda x: x[2])
            return empty_cells
        
        def solve_recursive():
            """Giải đệ quy với ghi lại từng bước"""
            empty_cells = get_empty_cells_with_constraints()
            
            if not empty_cells:
                self.steps.append({
                    'step_number': len(self.steps),
                    'description': '🎉 Đã giải xong Sudoku!',
                    'grid': [row[:] for row in solution],
                    'current_cell': None,
                    'possible_values': {},
                    'action': 'complete',
                    'conflicts': []
                })
                return True
            
            # Chọn ô có ít lựa chọn nhất (MRV heuristic)
            row, col, num_possible, possible_values = empty_cells[0]
            
            # Ghi lại bước chọn ô
            self.steps.append({
                'step_number': len(self.steps),
                'description': f'Chọn ô ({row+1}, {col+1}) - có {num_possible} giá trị khả dĩ: {possible_values}',
                'grid': [row[:] for row in solution],
                'current_cell': (row, col),
                'possible_values': {f'{row}-{col}': possible_values},
                'action': 'select_cell',
                'conflicts': []
            })
            
            if num_possible == 0:
                # Không có giá trị nào có thể điền -> backtrack
                self.steps.append({
                    'step_number': len(self.steps),
                    'description': f'❌ Ô ({row+1}, {col+1}) không có giá trị hợp lệ - Backtrack!',
                    'grid': [row[:] for row in solution],
                    'current_cell': (row, col),
                    'possible_values': {},
                    'action': 'backtrack',
                    'conflicts': []
                })
                return False
            
            for value in possible_values:
                # Thử giá trị
                solution[row][col] = value
                
                self.steps.append({
                    'step_number': len(self.steps),
                    'description': f'Thử giá trị {value} vào ô ({row+1}, {col+1})',
                    'grid': [row[:] for row in solution],
                    'current_cell': (row, col),
                    'possible_values': {},
                    'action': 'try_value',
                    'conflicts': []
                })
                
                # Kiểm tra constraint propagation
                propagation_successful = True
                affected_cells = self.get_affected_cells(row, col)
                
                # Ghi lại ảnh hưởng đến các ô khác
                if affected_cells:
                    updated_possibilities = {}
                    for r, c in affected_cells:
                        if solution[r][c] == 0:
                            new_possible = self.get_possible_values(solution, r, c)
                            updated_possibilities[f'{r}-{c}'] = new_possible
                            if len(new_possible) == 0:
                                propagation_successful = False
                    
                    self.steps.append({
                        'step_number': len(self.steps),
                        'description': f'Cập nhật ràng buộc cho {len(affected_cells)} ô liên quan',
                        'grid': [row[:] for row in solution],
                        'current_cell': (row, col),
                        'possible_values': updated_possibilities,
                        'action': 'propagate',
                        'conflicts': []
                    })
                
                if propagation_successful and solve_recursive():
                    return True
                
                # Backtrack
                solution[row][col] = 0
                self.steps.append({
                    'step_number': len(self.steps),
                    'description': f'⬅️ Backtrack: Xóa {value} khỏi ô ({row+1}, {col+1})',
                    'grid': [row[:] for row in solution],
                    'current_cell': (row, col),
                    'possible_values': {},
                    'action': 'backtrack',
                    'conflicts': []
                })
            
            return False
        
        # Bắt đầu giải
        success = solve_recursive()
        
        if not success:
            self.steps.append({
                'step_number': len(self.steps),
                'description': '❌ Không tìm được lời giải',
                'grid': [row[:] for row in solution],
                'current_cell': None,
                'possible_values': {},
                'action': 'no_solution',
                'conflicts': []
            })
        
        return self.steps
    
    def get_affected_cells(self, row, col):
        """Lấy danh sách các ô bị ảnh hưởng khi điền số vào ô (row, col)"""
        affected = set()
        
        # Hàng
        for c in range(9):
            if c != col:
                affected.add((row, c))
        
        # Cột
        for r in range(9):
            if r != row:
                affected.add((r, col))
        
        # Ô 3x3
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for r in range(start_row, start_row + 3):
            for c in range(start_col, start_col + 3):
                if (r, c) != (row, col):
                    affected.add((r, c))
        
        return list(affected)
    
    def generate_puzzle(self, difficulty='medium'):
        """Tạo puzzle Sudoku có solution"""
        puzzles = {
            'easy': [
                [5, 3, 0, 0, 7, 0, 0, 0, 0],
                [6, 0, 0, 1, 9, 5, 0, 0, 0],
                [0, 9, 8, 0, 0, 0, 0, 6, 0],
                [8, 0, 0, 0, 6, 0, 0, 0, 3],
                [4, 0, 0, 8, 0, 3, 0, 0, 1],
                [7, 0, 0, 0, 2, 0, 0, 0, 6],
                [0, 6, 0, 0, 0, 0, 2, 8, 0],
                [0, 0, 0, 4, 1, 9, 0, 0, 5],
                [0, 0, 0, 0, 8, 0, 0, 7, 9]
            ],
            'medium': [
                [0, 2, 0, 6, 0, 8, 0, 0, 0],
                [5, 8, 0, 0, 0, 9, 7, 0, 0],
                [0, 0, 0, 0, 4, 0, 0, 0, 0],
                [3, 7, 0, 0, 0, 0, 5, 0, 0],
                [6, 0, 0, 0, 0, 0, 0, 0, 4],
                [0, 0, 8, 0, 0, 0, 0, 1, 3],
                [0, 0, 0, 0, 2, 0, 0, 0, 0],
                [0, 0, 9, 8, 0, 0, 0, 3, 6],
                [0, 0, 0, 3, 0, 6, 0, 9, 0]
            ],
            'hard': [
                [0, 0, 0, 6, 0, 0, 4, 0, 0],
                [7, 0, 0, 0, 0, 3, 6, 0, 0],
                [0, 0, 0, 0, 9, 1, 0, 8, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 5, 0, 1, 8, 0, 0, 0, 3],
                [0, 0, 0, 3, 0, 6, 0, 4, 5],
                [0, 4, 0, 2, 0, 0, 0, 6, 0],
                [9, 0, 3, 0, 0, 0, 0, 0, 0],
                [0, 2, 0, 0, 0, 0, 1, 0, 0]
            ]
        }
        
        return puzzles.get(difficulty, puzzles['medium'])

# Khởi tạo visualizer toàn cục
visualizer = SudokuVisualizer()

@app.route('/')
def index():
    return render_template('sudoku_visual.html')

@app.route('/api/generate_puzzle/<difficulty>')
def generate_puzzle(difficulty):
    """Tạo puzzle Sudoku mới"""
    puzzle = visualizer.generate_puzzle(difficulty)
    visualizer.set_grid(puzzle)
    
    return jsonify({
        'puzzle': puzzle,
        'difficulty': difficulty,
        'conflicts': visualizer.validate_input(puzzle)
    })

@app.route('/api/validate_input', methods=['POST'])
def validate_input():
    """Kiểm tra tính hợp lệ của input"""
    data = request.json
    grid = data.get('grid')
    
    if not grid:
        return jsonify({'error': 'Không có dữ liệu'})
    
    conflicts = visualizer.validate_input([row[:] for row in grid])
    
    return jsonify({
        'conflicts': conflicts,
        'is_valid': len(conflicts) == 0
    })

@app.route('/api/solve_step_by_step', methods=['POST'])
def solve_step_by_step():
    """Giải Sudoku từng bước"""
    data = request.json
    grid = data.get('grid')
    
    if not grid:
        return jsonify({'error': 'Không có dữ liệu'})
    
    # Kiểm tra conflicts trước khi giải
    conflicts = visualizer.validate_input([row[:] for row in grid])
    if conflicts:
        return jsonify({
            'error': 'Sudoku có lỗi conflicts',
            'conflicts': conflicts
        })
    
    visualizer.set_grid(grid)
    steps = visualizer.solve_step_by_step()
    
    return jsonify({
        'success': True,
        'steps': steps,
        'total_steps': len(steps)
    })

@app.route('/api/get_graph_info')
def get_graph_info():
    """Lấy thông tin về đồ thị ràng buộc"""
    visualizer.build_constraint_graph()
    
    total_cells = 81
    total_constraints = sum(len(neighbors) for neighbors in visualizer.graph.values()) // 2
    
    return jsonify({
        'total_cells': total_cells,
        'total_constraints': total_constraints,
        'max_colors': 9,
        'graph_density': round(total_constraints / (total_cells * (total_cells - 1) // 2), 4)
    })

@app.route('/api/get_cell_possibilities', methods=['POST'])
def get_cell_possibilities():
    """Lấy các giá trị khả dĩ cho tất cả các ô trống"""
    data = request.json
    grid = data.get('grid')
    
    if not grid:
        return jsonify({'error': 'Không có dữ liệu'})
    
    possibilities = {}
    for i in range(9):
        for j in range(9):
            if grid[i][j] == 0:
                possible = visualizer.get_possible_values(grid, i, j)
                possibilities[f'{i}-{j}'] = possible
    
    return jsonify({'possibilities': possibilities})

if __name__ == '__main__':
    app.run(debug=True)