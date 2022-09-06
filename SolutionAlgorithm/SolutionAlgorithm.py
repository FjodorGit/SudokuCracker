import numpy as np
from collections import deque
import copy

#TODO: Refactoring, improve state management
class Solution:

    square = dict() 
    stateStack = deque()

    def __init__(self) -> None:

        squareCoord = [(i,j) for i in range(3) for j in range(3)]
        translations = [(i,j) for i in [0,3,6] for j in [0,3,6]]
        for t in range(9):
            self.square.update({t: []})
            for s in range(9):
                self.square[t].append((squareCoord[s][0] + translations[t][0], squareCoord[s][1] + translations[t][1]))

    def addSinglePosibilityCondidates(self, emptyPos, board, numEmpty):
        possible = False
        for pos, nums in emptyPos.copy().items():
            if len(nums) == 1:
                possible = True
                number = nums.pop(0)
                board[pos[0]][pos[1]] = number
                emptyPos = self.updateEmptyPositions(emptyPos, pos, number)
                numEmpty = self.updateNumberPositions(numEmpty, pos, number)

        return emptyPos, board, numEmpty, possible

    def addUnambiguousNumbers(self, numEmpty, board, emptyPos):
        upositions = set()
        for num, positions in numEmpty.copy().items():
            availableSpotsInSquare = {i:np.empty([0,2]).astype(int) for i in range(9)}

            for r,c in positions:
                availableSpotsInSquare[self.getSquareFromCoord((r,c))] = np.vstack((availableSpotsInSquare[self.getSquareFromCoord((r,c))], np.array([[r,c]])))

                if np.count_nonzero(positions[:,0] == r) == 1:
                     upositions.add((r,c, num))

                if np.count_nonzero(positions[:,1] == c) == 1:
                     upositions.add((r,c, num))

            for s in range(9):
                if len(availableSpotsInSquare[s]) == 1:
                    upositions.add((availableSpotsInSquare[s][0][0], availableSpotsInSquare[s][0][1], num))
        
        if len(upositions) == 0:
            return numEmpty, board, emptyPos, False
        
        for r,c,n in upositions:
            board[r][c] = n
            numEmpty = self.updateNumberPositions(numEmpty, (r,c), n)
            emptyPos = self.updateEmptyPositions(emptyPos, (r,c), n)
        
        return numEmpty, board, emptyPos, True


    def updateEmptyPositions(self, emptyPos, pos, number):
        if pos in emptyPos.keys():
            emptyPos.pop(pos)
        for i in range(9):
            if (i, pos[1]) in emptyPos.keys() and number in emptyPos[(i, pos[1])]:
                emptyPos[(i, pos[1])].remove(number)
            if (pos[0], i) in emptyPos.keys() and number in emptyPos[(pos[0], i)]:
                emptyPos[(pos[0], i)].remove(number)

        for s in self.square[self.getSquareFromCoord((pos))]:
            if s in emptyPos.keys() and number in emptyPos[s]:
                emptyPos[s].remove(number)
        
        return emptyPos

    def updateNumberPositions(self, numEmpty, pos, number):
        for k, positions in numEmpty.items():
            index = np.where((positions == np.array(pos)).all(axis=1))
            numEmpty[k] = np.delete(positions, index, axis=0)

        indecesToDelete = []
        for i in range(len(numEmpty[number])):
            positionToCheck = tuple(numEmpty[number][i])
            if self.getSquareFromCoord(positionToCheck) == self.getSquareFromCoord(pos) or positionToCheck[0] == pos[0] or positionToCheck[1] == pos[1]:
                indecesToDelete.append(i)

        numEmpty[number] = np.delete(numEmpty[number], indecesToDelete, axis=0)
        return numEmpty
    
    def createAssumption(self, emptyPos, board, numsEmpty):
        min = 9
        bestPosition = (0,0)
        for pos, nums in emptyPos.copy().items():
            if len(nums) == 2:
                bestPosition = pos
                break

            if len(nums) < min:
                bestPosition = pos
                min = len(nums)

        if len(emptyPos[bestPosition]) == 0:
            emptyPos, board, numsEmpty = self.stateStack.pop()
            return emptyPos, board, numsEmpty
            
        number = emptyPos[bestPosition].pop(0)
        boardToCheck = copy.deepcopy(board)
        boardToCheck[bestPosition[0]][bestPosition[1]] = number
        postAssumptionPos = copy.deepcopy(emptyPos)
        postAssumptionNums = copy.deepcopy(numsEmpty)
        postAssumptionPos = self.updateEmptyPositions(postAssumptionPos, pos, number)
        postAssumptionNums = self.updateNumberPositions(postAssumptionNums, pos, number)
        violation = self.checkForViolation(postAssumptionPos, postAssumptionNums, boardToCheck)
        if violation:
            emptyPos, board, numsEmpty = self.stateStack.pop()
            return emptyPos, board, numsEmpty

        self.stateStack.append(( copy.deepcopy(emptyPos), copy.deepcopy(board), copy.deepcopy(numsEmpty)))
        board = boardToCheck

        return postAssumptionPos, board, postAssumptionNums

    def checkForViolation(self, emptyPos, numsEmpty, board):
        for _, nums in emptyPos.items():
            if len(nums) == 0:
                return True

        #TODO: create violation Check with numsEmpty

        for n, positions in numsEmpty.items():

            for i in range(9):

                inSquare_i = False
                for r,c in self.square[i]:
                    if board[r][c] == n:
                        inSquare_i = True
                        break

                possiblePosInSquare = False
                for p in positions:
                    if tuple(p) in self.square[i]:
                        possiblePosInSquare = True
                        break

                if not inSquare_i and not possiblePosInSquare:
                    return True

                if i not in positions[:,0] and n not in board[i]:
                    return True

                if i not in positions[:,1] and n not in board[:,i]:
                    return True

            

        
        return False

    def getSquareFromCoord(self, Coord: tuple):
        squareID = {(0,0):0, (0,1):1, (0,2):2, (1,0):3, (1,1):4, (1,2):5, (2,0):6, (2,1):7, (2,2):8}
        return squareID[(int(Coord[0] / 3), int(Coord[1] / 3))]

    def solveSudoku(self, board: list[list[str]]) -> None:
        '''
        Inittialize square
        '''
        emptyPos: dict[tuple, list[int]] = dict()

        matrixBoard = np.empty((9,9))
        for i in range(9):
            for j in range(9):
                if board[i][j] != ".":
                    matrixBoard[i][j] = int(board[i][j]) - 1
                    continue

                matrixBoard[i][j] = np.nan

        
        '''
        Empty Squares, Number positions, Numbers in row, Numbers in Col, Numbers in Square
        '''
        numRow = {i:np.array([]) for i in range(9)}
        numCol = {i:np.array([]) for i in range(9)}
        numSquare = {i:np.array([]) for i in range(9)}
        numPos = dict()
        numEmpty = dict()
        for i in range(9):
            numEmpty.update({i:np.empty([0,2]).astype(int)})
            for j in range(9):
                if board[i][j] != ".":
                    num = int(board[i][j]) - 1
                    numRow[i] = np.hstack((numRow[i], num))
                    numCol[j] = np.hstack((numCol[j], num))
                    numSquare[self.getSquareFromCoord((i,j))] = np.hstack((numSquare[self.getSquareFromCoord((i,j))], num))
                    numPos.update({(i,j): num})
                    continue
                emptyPos.update({(i,j):[]})


        '''
        Find possible value for every free pos
        '''
        for i in range(9):
            for j in range(9):
                for zahl in range(9):
                    if (i,j) not in numPos.keys() and zahl not in numRow[i] and zahl not in numCol[j] and zahl not in numSquare[self.getSquareFromCoord((i,j))]:
                        emptyPos[(i,j)].append(zahl)
                        numEmpty[zahl] = np.vstack((numEmpty[zahl], np.array([i,j])))

        self.stateStack.append((copy.deepcopy(emptyPos), copy.deepcopy(matrixBoard), copy.deepcopy(numEmpty)))
        while True:
            unambiguousPos = True
            unambiguousNum = True
            while unambiguousNum or unambiguousPos:
                emptyPos, matrixBoard, numEmpty, unambiguousPos = self.addSinglePosibilityCondidates(emptyPos, matrixBoard, numEmpty)
                numEmpty, matrixBoard, emptyPos, unambiguousNum = self.addUnambiguousNumbers(numEmpty, matrixBoard, emptyPos)
                if len(emptyPos) == 0:
                    for i in range(9):
                        for j in range(9):
                            board[i][j] = str(int(matrixBoard[i][j] + 1))
                    return

            emptyPos, matrixBoard, numEmpty = self.createAssumption(emptyPos, matrixBoard, numEmpty)
            
        

sol = Solution()
board = [["1",".",".",".",".",".",".","8","9"],[".",".",".",".",".","9",".",".","2"],[".",".",".",".",".",".","4","5","."],[".",".","7","6",".",".",".",".","."],[".","3",".",".","4",".",".",".","."],["9",".",".",".",".","2",".",".","5"],[".",".","4",".","7",".",".",".","."],["5",".",".",".",".","8",".","1","."],[".","6",".","3",".",".",".",".","."]]
print(sol.solveSudoku(board))
