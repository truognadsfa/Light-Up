import numpy as np
import copy
import time
import heapq
import pygame
import sys

"""Min priority queue"""
class PriorityQueue:
    
    def  __init__(self):
        self.Heap = []
        self.Count = 0

    def enqueue(self, priority, item):
        entry = (priority, self.Count, item)
        heapq.heappush(self.Heap, entry)
        self.Count += 1

    def dequeue(self):
        (_, _, item) = heapq.heappop(self.Heap)
        return item

    def isEmpty(self):
        return len(self.Heap) == 0

class LightUpSolver:

    def __init__(self) -> None:
        pass

    def is_valid_cell_value(self, cell):
        if (cell < -1) or (cell > 7): return False
        return True

    # load puzzle matrix for solving
    def load_puzzle(self, level, puzzle_file):
        self.matrix = []
        if level < 0:
            print("ERROR: Level "+str(level)+" is out of range.")
            sys.exit(1)
        else:
            file = open(puzzle_file,'r')
            level_found = False
            for line in file:
                row = []
                if not level_found:
                    if  "Level "+str(level) == line.strip():
                        level_found = True
                else:
                    if line.strip() != "":
                        row = []
                        for c in line:
                            if c == '-': 
                                row.append(c)
                            elif c != '\n' and self.is_valid_cell_value(int(c)):
                                row.append(c)
                            elif c == '\n':
                                continue
                            else:
                                print("ERROR: Level "+str(level)+" has invalid value "+c)
                                sys.exit(1)
                        self.matrix.append(row)
                    else:
                        break
        
        puzzle_matrix = []
        for r in self.matrix:
            puzzle_matrix.append((np.array([int(x) if x != '-' else -1 for x in r])))
        
        self.puzzle_matrix = np.array(puzzle_matrix)
        self.puzzle_matrix_shape = self.puzzle_matrix.shape
        self.white_cell_positions = tuple(tuple(x) for x in np.argwhere(self.puzzle_matrix == 5))

        # All numbered black cell positions
        self.numbered_black_cells = np.argwhere((self.puzzle_matrix <= 4)&(self.puzzle_matrix >= 0))

        # All positions that are adjacent to numbered black cells (this is used for heuristic function)
        self.around_numbered_black_cell = []
        for r,c in self.numbered_black_cells:
            if r-1 >= 0 and puzzle_matrix[r-1][c] == 5:
                if (r-1,c) not in self.around_numbered_black_cell:
                    self.around_numbered_black_cell.append((r-1,c))
            if r+1 < self.puzzle_matrix_shape[0] and puzzle_matrix[r+1][c] == 5:
                if (r+1,c) not in self.around_numbered_black_cell:
                    self.around_numbered_black_cell.append((r+1,c))
            if c-1 >= 0 and puzzle_matrix[r][c-1] == 5:
                if (r,c-1) not in self.around_numbered_black_cell:
                    self.around_numbered_black_cell.append((r,c-1))
            if c+1 < self.puzzle_matrix_shape[1] and puzzle_matrix[r][c+1] == 5:
                if (r,c+1) not in self.around_numbered_black_cell:
                    self.around_numbered_black_cell.append((r,c+1))

    def update_state(self, white_cell_positions, new_light_position):
        white_cell_positions = list(white_cell_positions)
        white_cell_positions.remove(new_light_position)
        r, c = new_light_position

        # update row
        i = 1
        while (r+i < self.puzzle_matrix_shape[0]):
            if self.puzzle_matrix[r+i][c] < 5:
                break
            if (r+i,c) in white_cell_positions:
                white_cell_positions.remove((r+i,c))
            i+=1
        
        i = 1
        while (r-i >= 0):
            if self.puzzle_matrix[r-i][c] < 5:
                break
            if (r-i,c) in white_cell_positions:
                white_cell_positions.remove((r-i,c))
            i+=1

        # update column
        j = 1
        while (c+j < self.puzzle_matrix_shape[1]):
            if self.puzzle_matrix[r][c+j] < 5:
                break
            if (r,c+j) in white_cell_positions:
                white_cell_positions.remove((r,c+j))
            j+=1

        j = 1
        while (c-j >= 0):
            if self.puzzle_matrix[r][c-j] < 5:
                break
            if (r,c-j) in white_cell_positions:
                white_cell_positions.remove((r,c-j))
            j+=1
        
        return tuple(white_cell_positions)

    def black_cell_status(self, black_cell_position, white_cell_positions, light_positions):
        r, c = black_cell_position
        around_light = 0

        if (r-1,c) in light_positions: around_light+=1
        if (r+1,c) in light_positions: around_light+=1
        if (r,c-1) in light_positions: around_light+=1
        if (r,c+1) in light_positions: around_light+=1

        around_white_cell = 0

        if (r-1,c) in white_cell_positions: around_white_cell+=1
        if (r+1,c) in white_cell_positions: around_white_cell+=1
        if (r,c-1) in white_cell_positions: around_white_cell+=1
        if (r,c+1) in white_cell_positions: around_white_cell+=1
        
        # status = number of around lights - the number in the black cell
        # status > 0: invalid black cell
        # status == 0: satisfied black cell
        # status < 0: unsatisfied black cell

        if self.puzzle_matrix[r][c] < around_light:
            return -1
        elif self.puzzle_matrix[r][c] == around_light:
            return 1
        elif self.puzzle_matrix[r][c] - around_light > around_white_cell:
            return -1
        
        return 0

    def is_dead_state(self, white_cell_positions, light_positions):
        for c in self.numbered_black_cells:
            if self.black_cell_status(c, white_cell_positions, light_positions) < 0:
                return True   
        return False

    def is_goal_state(self, white_cell_positions, light_positions):

        # if all white cells are lit:
        if white_cell_positions == ():
            return True
        return False

    def add_new_light_position(self, light_positions, new_light_position):
        light_positions = list(light_positions)
        light_positions.append(new_light_position)
        light_positions = sorted(light_positions)
        return tuple(light_positions)
        
    def dfs(self):
        state_stack = [(self.white_cell_positions, ())]

        explored_state = set()

        while (state_stack):
            white_cell_positions, light_positions = state_stack.pop()
            
            if (light_positions not in explored_state) and (not self.is_dead_state(white_cell_positions, light_positions)):
                if self.is_goal_state(white_cell_positions, light_positions):
                    return white_cell_positions, light_positions
                    
                explored_state.add(light_positions)
                
                for new_light_position in white_cell_positions:
                    new_light_positions = self.add_new_light_position(light_positions, new_light_position)
                    new_white_cell_positions = self.update_state(white_cell_positions, new_light_position)
                    state_stack.append((new_white_cell_positions, new_light_positions))
       
        return () 

    def heuristic(self, white_cell_positions, light_position, new_light_position):
        value = 10
        # for each satisfied numbered black cell, state priority increase 1
        for c in self.numbered_black_cells:
            if self.black_cell_status(c, white_cell_positions, light_position) == 1: 
                value-=1

        # new light bulb position is beside a numbered black cell, state priority increase 1
        if tuple(new_light_position) in self.around_numbered_black_cell:
            value-=1
        
        return value

    def a_star(self):
        priority_queue = PriorityQueue()
        priority_queue.enqueue(0, (self.white_cell_positions, ()))

        explored_state = set()

        while (priority_queue):
            white_cell_positions, light_positions = priority_queue.dequeue()
            
            if (light_positions not in explored_state) and (not self.is_dead_state(white_cell_positions, light_positions)):
                if self.is_goal_state(white_cell_positions, light_positions):
                    return white_cell_positions, light_positions
                    
                explored_state.add(light_positions)
                for new_light_position in white_cell_positions:
                    light_position_update = self.add_new_light_position(light_positions, new_light_position)
                    new_puzzle_matrix = self.update_state(white_cell_positions,new_light_position)
                    priority_queue.enqueue(self.heuristic(white_cell_positions, light_position_update, new_light_position), (new_puzzle_matrix, light_position_update))
       
        return () 

    def get_solution(self, algorithm):
        if algorithm == 'dfs':
            return self.dfs()
        elif algorithm == 'a_star':
            return self.a_star()
        else:
            raise Exception('Invalid algorithm.')

class LightUpDisplayer:

    def __init__(self, puzzle_file) -> None:
        self.wall = pygame.image.load('images/wall.png')
        self.wall0 = pygame.image.load('images/wall0.png')
        self.wall1 = pygame.image.load('images/wall1.png')
        self.wall2 = pygame.image.load('images/wall2.png')
        self.wall3 = pygame.image.load('images/wall3.png')
        self.wall4 = pygame.image.load('images/wall4.png')
        self.lit = pygame.image.load('images/lit.png')
        self.dark = pygame.image.load('images/dark.png')
        self.light = pygame.image.load('images/light.png')
        self.background = 255, 255, 255
        pygame.init()
        pygame.display.set_caption('Light Up')

        self.puzzle_file = puzzle_file
        self.level = self.start_puzzle()
        self.load_puzzle(self.level)
        self.display_box(pygame.display.set_mode(self.get_puzzle_size()),'Solving...')

        self.light_position = []
        self.numbered_black_cells = np.argwhere((self.puzzle_matrix <= 4)&(self.puzzle_matrix >= 0))
        self.initial_puzzle_matrix = copy.deepcopy(self.puzzle_matrix)

    def start_puzzle(self):
        start = pygame.display.set_mode((490,490))
        level = self.select_level(start,"Select Level")
        if int(level) > 0:
            print('Level: '+level)
            return int(level)
        else:
            print("ERROR: Invalid Level: "+str(level))
            sys.exit(2)

    def is_valid_cell_value(self, cell):
        if (cell < -1) or (cell > 7): return False
        return True

    def load_puzzle(self, level):
        self.matrix = []
        if level < 0:
            print("ERROR: Level "+str(level)+" is out of range.")
            sys.exit(1)
        else:
            file = open(self.puzzle_file,'r')
            level_found = False
            for line in file:
                row = []
                if not level_found:
                    if  "Level "+str(level) == line.strip():
                        level_found = True
                else:
                    if line.strip() != "":
                        row = []
                        for c in line:
                            if c == '-': 
                                row.append(c)
                            elif c != '\n' and self.is_valid_cell_value(int(c)):
                                row.append(c)
                            elif c == '\n':
                                continue
                            else:
                                print("ERROR: Level "+str(level)+" has invalid value "+c)
                                sys.exit(1)
                        self.matrix.append(row)
                    else:
                        break
        
        puzzle_matrix = []
        for r in self.matrix:
            puzzle_matrix.append((np.array([int(x) if x != '-' else -1 for x in r])))
        
        self.puzzle_matrix = np.array(puzzle_matrix)

    def get_puzzle_size(self):
        x = 0
        y = len(self.matrix)
        for row in self.matrix:
            if len(row) > x:
                x = len(row)
        return (x * 70, y * 70)
    
    def display_puzzle(self, matrix, screen):
        screen.fill(self.background)
        x = 0
        y = 0
        for row in matrix:
            for num in row:
                if num == -1:
                    screen.blit(self.wall,(x,y))
                elif num == 0:
                    screen.blit(self.wall0,(x,y))
                elif num == 1:
                    screen.blit(self.wall1,(x,y))
                elif num == 2:
                    screen.blit(self.wall2,(x,y))
                elif num == 3:
                    screen.blit(self.wall3,(x,y))
                elif num == 4:
                    screen.blit(self.wall4,(x,y))
                elif num == 5:
                    screen.blit(self.dark,(x,y))
                elif num == 6 or num == 7:
                    screen.blit(self.lit,(x,y))
                elif num == 8:
                    screen.blit(self.light,(x,y))
                x = x + 70
            x = 0
            y = y + 70

    def get_key(self):
        while 1:
            event = pygame.event.poll()
            if event.type == pygame.KEYDOWN:
                return event.key
            else:
                pass

    def display_box(self, screen, message):
        scaling_light = pygame.transform.scale(self.light, (100, 100))
        screen.blit(scaling_light,(195, 50))
        "Print a message in a box in the middle of the screen"
        fontobject = pygame.font.Font(None,30)
        pygame.draw.rect(screen, (0,0,0),
                    ((screen.get_width() / 2) - 100,
                        (screen.get_height() / 2) - 10,
                        200,20), 0)
        pygame.draw.rect(screen, (255,255,255),
                    ((screen.get_width() / 2) - 105,
                        (screen.get_height() / 2) - 15,
                        210,30), 1)
        if len(message) != 0:
            screen.blit(fontobject.render(message, 1, (255,255,255)),
                    ((screen.get_width() / 2) - 100, (screen.get_height() / 2) - 10))

        fontobject = pygame.font.Font(None,50)
        screen.blit(
            fontobject.render(
                "LIGHT UP", 1, (255,255,255)
                ),
                (screen.get_width() / 2 - 80, 170)
            )

        fontobject = pygame.font.Font(None,20)
        screen.blit(
            fontobject.render(
                "- Click on the white cell to place the light bulb.", 1, (255,255,255)
                ),
                (100, (screen.get_height() / 2) + 50)
            )
        
        screen.blit(
            fontobject.render(
                "- Click on the light bulb to remove it.", 1, (255,255,255)
                ),
                (100, (screen.get_height() / 2) + 70)
            )

        screen.blit(
            fontobject.render(
                "- Press 's' to show the solution.", 1, (255,255,255)
                ),
                (100, (screen.get_height() / 2) + 90)
            )

        screen.blit(
            fontobject.render(
                "- Press 'c' to continue you gameplay.", 1, (255,255,255)
                ),
                (100, (screen.get_height() / 2) + 110)
            )

        screen.blit(
            fontobject.render(
                "- Press 'r' to restart.", 1, (255,255,255)
                ),
                (100, (screen.get_height() / 2) + 130)
            )

        screen.blit(
            fontobject.render(
                "- Press 'q' to quit.", 1, (255,255,255)
                ),
                (100, (screen.get_height() / 2) + 150)
            )

        screen.blit(
            fontobject.render(
                "The 'Complete' board will be displayed if you win.", 1, (255,255,255)
                ),
                (100, (screen.get_height() / 2) + 170)
            )

        pygame.display.flip()

    def display_end(self, screen):
        message = "Level Completed."
        fontobject = pygame.font.Font(None,30)
        pygame.draw.rect(screen, (0,0,0),
                    ((screen.get_width() / 2) - 105,
                        (screen.get_height() / 2) - 15,
                        210,30), 0)
        pygame.draw.rect(screen, (255,255,255),
                    ((screen.get_width() / 2) - 105,
                        (screen.get_height() / 2) - 15,
                        210,30), 1)
        screen.blit(fontobject.render(message, 1, (255,255,255)),
                    ((screen.get_width() / 2) - 100, (screen.get_height() / 2) - 10))
        pygame.display.flip()

    def select_level(self, screen, question):
        "ask(screen, question) -> answer"
        pygame.font.init()
        current_string = []
        self.display_box(screen, question + ": " + ''.join(current_string))
        while 1:
            inkey = self.get_key()
            if inkey == pygame.K_BACKSPACE:
                current_string = current_string[0:-1]
            elif inkey == pygame.K_RETURN:
                break
            elif inkey == pygame.K_MINUS:
                current_string.append("_")
            elif inkey <= 127:
                current_string.append(chr(inkey))
            self.display_box(screen, question + ": " + ''.join(current_string))
        return ''.join(current_string)

    def update_state(self, new_light_position):
        r, c = int(new_light_position[1]/70), int(new_light_position[0]/70)
        puzzle_matrix_shape = self.puzzle_matrix.shape
        if self.puzzle_matrix[r][c] == 5:
            self.puzzle_matrix[r][c] = 8
            self.light_position.append((r,c))

            i = 1
            while (r+i < puzzle_matrix_shape[0]):
                if self.puzzle_matrix[r+i][c] < 5:
                    break
                self.puzzle_matrix[r+i][c] += 1
                i+=1
            
            i = 1
            while (r-i >= 0):
                if self.puzzle_matrix[r-i][c] < 5:
                    break
                self.puzzle_matrix[r-i][c] += 1
                i+=1

            j = 1
            while (c+j < puzzle_matrix_shape[1]):
                if self.puzzle_matrix[r][c+j] < 5:
                    break
                self.puzzle_matrix[r][c+j] += 1
                j+=1

            j = 1
            while (c-j >= 0):
                if self.puzzle_matrix[r][c-j] < 5:
                    break
                self.puzzle_matrix[r][c-j] += 1
                j+=1
        elif self.puzzle_matrix[r][c] == 8:
            self.puzzle_matrix[r][c] = 5
            self.light_position.remove((r,c))

            i = 1
            while (r+i < puzzle_matrix_shape[0]):
                if self.puzzle_matrix[r+i][c] < 5:
                    break
                self.puzzle_matrix[r+i][c] -= 1
                i+=1
            
            i = 1
            while (r-i >= 0):
                if self.puzzle_matrix[r-i][c] < 5:
                    break
                self.puzzle_matrix[r-i][c] -= 1
                i+=1

            j = 1
            while (c+j < puzzle_matrix_shape[1]):
                if self.puzzle_matrix[r][c+j] < 5:
                    break
                self.puzzle_matrix[r][c+j] -= 1
                j+=1

            j = 1
            while (c-j >= 0):
                if self.puzzle_matrix[r][c-j] < 5:
                    break
                self.puzzle_matrix[r][c-j] -= 1
                j+=1

    def is_valid_black_cell(self, black_cell_position):
        r, c = black_cell_position
        around_light = 0

        if (r-1,c) in self.light_position: around_light+=1
        if (r+1,c) in self.light_position: around_light+=1
        if (r,c-1) in self.light_position: around_light+=1
        if (r,c+1) in self.light_position: around_light+=1
        
        if around_light != self.puzzle_matrix[r][c]:
            return False
        
        return True

    def is_goal_state(self):

        if (np.argwhere(self.puzzle_matrix == 5).size == 0):
            for c in self.numbered_black_cells:
                if not self.is_valid_black_cell(c): return False
            return True
        
        return False

def start_puzzle():
    displayer = LightUpDisplayer('puzzles')
    puzzle_size = displayer.get_puzzle_size()
    screen = pygame.display.set_mode(puzzle_size)

    solver = LightUpSolver()
    solver.load_puzzle(displayer.level, 'puzzles')

    start_time = time.time()
    solution = solver.get_solution(ALGORITHM)
    finish_time = time.time()
    print(ALGORITHM+': '+str(finish_time-start_time)+'s')

    puzzle = displayer.puzzle_matrix
    show_solution = False

    for white_cell in solver.white_cell_positions:
        solver.puzzle_matrix[white_cell] = 6
    for light in solution[1]:
        solver.puzzle_matrix[light] = 8

    while 1:
        displayer.display_puzzle(puzzle, screen)
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN and not show_solution:
                displayer.update_state(pygame.mouse.get_pos())
            if event.type == pygame.QUIT: sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q: sys.exit(0)
                elif event.key == pygame.K_s: 
                    if not show_solution:
                        print('Solution:', solution[1])
                        show_solution=True
                        puzzle = solver.puzzle_matrix
                        step = 0
                elif event.key == pygame.K_c:
                    puzzle = displayer.puzzle_matrix
                    show_solution = False
                elif event.key == pygame.K_r:
                    displayer.puzzle_matrix = copy.copy(displayer.initial_puzzle_matrix)
                    puzzle = displayer.puzzle_matrix
                    show_solution = False

        if displayer.is_goal_state():
            displayer.display_end(screen)

        pygame.display.update()

def get_result():
    total_time = 0
    solver = LightUpSolver()
    f = open(ALGORITHM+'_result', 'w')
    for i in range(1,51):
        solver.load_puzzle(i, 'puzzles')   
        s = time.time()
        result = solver.get_solution(ALGORITHM)
        e = time.time()
        total_time+=e-s
        f.write('Level '+str(i)+': '+str(e-s)+' s.\n')
    f.write('Total time: '+str(total_time)+' s\n')
    f.close()

# 'dfs' or 'a_star'
ALGORITHM = 'dfs'

start_puzzle()
#get_result()