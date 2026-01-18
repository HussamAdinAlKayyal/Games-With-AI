import random
from collections import deque
import time
import heapq


TRUE: str = '🟩'
FALSE: str = '🟥'

ACTION_COSTS = {
    TRUE: 1,
    FALSE: 2
}


def enter_int(message: str):
    while True:
        num = input(message)
        not_int = False
        for i in range(len(num)):
            if not num[i].isdigit():
                not_int = True
                break
        if not_int:
            print('Please enter a number: ')
            continue
        return int(num)


class PuzzleState:
    def __init__(self, *args):
        if len(args) == 2 and isinstance(args[0], int) and isinstance(args[1], int):
            self.row = args[0]
            self.col = args[1]
            self.board = [[FALSE if random.randint(0, 1) == 1 else TRUE for _ in range(self.col)] for _ in range(self.row)]
        elif len(args) == 3 and isinstance(args[0], int) and isinstance(args[1], int) and isinstance(args[2], bool):
            self.row = args[0]
            self.col = args[1]
            if args[2]:
                self.board = self.get_goal()
                self.shuffle_board()
            else:
                self.board = [[FALSE if random.randint(0, 1) == 1 else TRUE for _ in range(self.col)] for _ in range(self.row)]
        elif len(args) == 1 and isinstance(args[0], list):
            self.row = len(args[0])
            self.col = len(args[0][0])
            self.board = args[0]
        self.value_of_cell_before_changing = ' '
        self.changed_x = -1
        self.changed_y = -1

    def shuffle_board(self, steps=10):
        for _ in range(steps):
            rand_r = random.randint(0, self.row - 1)
            rand_c = random.randint(0, self.col - 1)
            self.apply_action_on_board(rand_r, rand_c)

    def apply_action_on_board(self, x: int, y: int):
        self.try_invert(self, x, y)
        self.try_invert(self, x, y - 1)
        self.try_invert(self, x, y + 1)
        self.try_invert(self, x - 1, y)
        self.try_invert(self, x + 1, y)

    def get_goal(self):
        return [[TRUE for _ in range(self.col)] for _ in range(self.row)]

    def is_goal(self):
        goal = self.get_goal()
        for i in range(self.row):
            for j in range(self.col):
                if self.board[i][j] != goal[i][j]:
                    return False
        return True

    def __getitem__(self, item):
        return self.board[item]

    def __hash__(self):
        return hash(tuple(tuple(i) for i in self.board))

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def get_heuristic(self):
        count: int = 0
        for i in range(self.row):
            for j in range(self.col):
                if self.board[i][j] == FALSE:
                    count += 1
        return count / 5

    def get_value_of_cell_before_changing(self):
        return self.value_of_cell_before_changing

    def copy(self):
        state: PuzzleState = PuzzleState(self.row, self.col)
        for i in range(self.row):
            for j in range(self.col):
                state[i][j] = self.board[i][j]
        return state

    def print(self) -> None:
        for i in range(self.row):
            for j in range(self.col):
                print(self.board[i][j], end='')
                if j != self.col - 1:
                    print('|', end='')
            print()

    def try_invert(self, state, i: int, j: int) -> bool:
        if 0 <= i < self.row and 0 <= j < self.col:
            state[i][j] = FALSE if state[i][j] == TRUE else TRUE
            return True
        return False

    def apply_action(self, x: int, y: int):

        new_state = self.copy()
        if not self.try_invert(new_state, x, y):
            return None
        new_state.value_of_cell_before_changing = self.board[x][y]
        new_state.changed_x, new_state.changed_y = x, y
        self.try_invert(new_state, x, y + 1)
        self.try_invert(new_state, x, y - 1)
        self.try_invert(new_state, x + 1, y)
        self.try_invert(new_state, x - 1, y)
        return new_state

    def get_next_states(self):
        states: list[PuzzleState] = []
        for i in range(self.row):
            for j in range(self.col):
                states.append(self.apply_action(i, j))
        return states


class GridPuzzleGame:
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col
        self.puzzle_state = PuzzleState(row, col)

    def enter_coordinate_value(self, coordinate: str):
        if coordinate == 'X':
            return enter_int(f'Enter the {coordinate} coordinate of the cell you choose ({coordinate} is between 0 and {self.row - 1}): ')
        if coordinate == 'Y':
            return enter_int(f'Enter the {coordinate} coordinate of the cell you choose ({coordinate} is between 0 and {self.col - 1}): ')
        return 0

    def does_reach_the_goal(self) -> bool:
        return self.puzzle_state.is_goal()

    def apply_action(self, x: int, y: int):
        return self.puzzle_state.apply_action(x, y)

    def start(self):
        while True:
            self.puzzle_state.print()
            x: int = self.enter_coordinate_value('X')
            y: int = self.enter_coordinate_value('Y')
            ps = self.apply_action(x, y)
            if ps is None:
                print('You entered wrong inputs, try again.')
                continue
            self.puzzle_state = ps
            if self.does_reach_the_goal():
                self.puzzle_state.print()
                print('YOU WIN!')
                break


class PuzzleNode:
    def __init__(self, state: PuzzleState, parent=None, path_cost: int = 0):
        self.state: PuzzleState = state
        self.path_cost: int = path_cost
        self.parent: PuzzleNode = parent

    def __lt__(self, other):
        return self.path_cost < other.path_cost

    def __hash__(self):
        return self.state.__hash__()

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()


class AStarNode(PuzzleNode):
    def __init__(self, state: PuzzleState, parent=None, path_cost=0, heuristic=0.0):
        super().__init__(state, parent, path_cost)
        self.heuristic = heuristic
        self.f_cost: float = path_cost + heuristic

    def __lt__(self, other):
        return self.f_cost < other.f_cost


class SearchAlgorithm:
    @staticmethod
    def get_solution_path(node: PuzzleNode):
        path_states = []
        current = node
        while current.parent is not None:
            path_states.append(current.state)
            current = current.parent
        path_states.append(current.state)
        path_states.reverse()
        return path_states

    @staticmethod
    def solve_dfs(start_state: PuzzleState):
        start_node: PuzzleNode = PuzzleNode(start_state)
        frontier = [start_node]
        explored = set()
        nodes_expanded = 0
        while frontier:
            current_node = frontier.pop()
            nodes_expanded += 1
            if current_node.state.is_goal():
                return current_node, nodes_expanded
            if current_node.state in explored:
                continue
            explored.add(current_node.state)
            for child_state in reversed(current_node.state.get_next_states()):
                child_node: PuzzleNode = PuzzleNode(child_state, current_node, current_node.path_cost + 1)
                if child_state not in explored:
                    frontier.append(child_node)
        return None, nodes_expanded

    @staticmethod
    def solve_bfs(start_state: PuzzleState):
        start_node: PuzzleNode = PuzzleNode(start_state)
        nodes_expanded: int = 0
        explored = set()
        frontier: deque = deque([start_node])
        while frontier:
            current_node: PuzzleNode = frontier.popleft()
            nodes_expanded += 1
            if current_node.state.is_goal():
                return current_node, nodes_expanded
            if current_node.state in explored:
                continue
            explored.add(current_node.state)
            for child_state in reversed(current_node.state.get_next_states()):
                child_node: PuzzleNode = PuzzleNode(child_state, current_node, current_node.path_cost + 1)
                if child_state not in explored:
                    frontier.append(child_node)
        return None, nodes_expanded

    @staticmethod
    def solve_ucs(start_state: PuzzleState):
        start_node = PuzzleNode(start_state, None, 0)
        pq: list[PuzzleNode] = []
        heapq.heappush(pq, start_node)
        explored = set()
        nodes_expanded = 0
        while pq:
            current_node = heapq.heappop(pq)
            if current_node.state.is_goal():
                return current_node, nodes_expanded
            if current_node.state in explored:
                continue
            explored.add(current_node.state)
            nodes_expanded += 1
            for child_state in current_node.state.get_next_states():
                step_cost = ACTION_COSTS.get(child_state.get_value_of_cell_before_changing())
                child_node = PuzzleNode(child_state, current_node, current_node.path_cost + step_cost)
                if child_state not in explored:
                    heapq.heappush(pq, child_node)
        return None, nodes_expanded

    @staticmethod
    def solve_a_star(start_state: PuzzleState):
        start_node: AStarNode = AStarNode(start_state)
        explored = set()
        nodes_expanded = 0
        pq: list[PuzzleNode] = []
        heapq.heappush(pq, start_node)
        while pq:
            current_node = heapq.heappop(pq)
            if current_node.state.is_goal():
                return current_node, nodes_expanded
            if current_node.state in explored:
                continue
            explored.add(current_node.state)
            for state in current_node.state.get_next_states():
                nodes_expanded += 1
                h_cost = state.get_heuristic()
                g_cost = current_node.path_cost + 1
                node: AStarNode = AStarNode(state, current_node, g_cost, h_cost)
                heapq.heappush(pq, node)
        return None, nodes_expanded


def run_and_print(solver_func, start_state, name):
    print(f"--- Running {name} ---")
    print("Start State:")
    start_state.print()
    start_time = time.time()
    solution_node, nodes_expanded = solver_func(start_state)
    end_time = time.time()
    print(f"\n--- Results for {name} ---")
    if solution_node:
        print(f"Solution Found!")
        print(f"   Path Length: {solution_node.path_cost} moves")
    else:
        print(f" No Solution Found.")
    print(f"   Nodes Expanded: {nodes_expanded}")
    print(f"   Time Taken: {end_time - start_time:.6f} seconds")
    print("========================================\n")
    if solution_node and solution_node.path_cost < 10:
        print("Solution Path:")
        path_states = SearchAlgorithm.get_solution_path(solution_node)
        for i, state in enumerate(path_states):
            if i == 0:
                print("Start:")
            else:
                print(f'Changed cell: ({state.changed_x}, {state.changed_y})')
            state.print()
            print("_____________________________________\n")
        print("========================================\n")


def main():
    def enter_row_and_col():
        while True:
            r = enter_int("Enter the number of rows you want: ")
            if r >= 2:
                break
            print("Number of rows must be greater than 2, try again: ")
        while True:
            c = enter_int("Enter the number of columns you want: ")
            if c >= 2:
                break
            print("Number of columns must be greater than 2, try again: ")
        return r, c

    print("---- Grid Light Puzzle ----")
    print("What do you want to do (choose 1 or 2):")
    print("\t1. Play the game by yourself.")
    print("\t2. Make the computer solve the game.")
    while True:
        choice = enter_int('Choose your choice (1 or 2): ')
        if choice == 1 or choice == 2:
            break
        print("You have to choose between 1 and 2: ", end='')
    if choice == 1:
        row, col = enter_row_and_col()
        game = GridPuzzleGame(row, col)
        game.start()
    elif choice == 2:
        row, col = enter_row_and_col()
        start_state: PuzzleState = PuzzleState(row, col, True)
        print("The initial state:")
        start_state.print()
        print("Choose which algorithm you want to solve the game:")
        print("\t1. DFS")
        print("\t2. BFS")
        print("\t3. UCS")
        print("\t4. A*")
        while True:
            choice = enter_int('Enter your choice from 1 to 4: ')
            if 1 <= choice <= 4:
                break
            print("You have to choose between 1 and 4, try again: ", end='')
        if choice == 1:
            solve_func = SearchAlgorithm.solve_dfs
            name = "DFS"
        elif choice == 2:
            solve_func = SearchAlgorithm.solve_bfs
            name = "BFS"
        elif choice == 3:
            solve_func = SearchAlgorithm.solve_ucs
            name = "UCS"
        else:
            solve_func = SearchAlgorithm.solve_a_star
            name = "A*"
        run_and_print(solver_func=solve_func, start_state=start_state, name=name)


if __name__ == '__main__':
    main()
