"""
Created by Joseph Edradan
Github: https://github.com/josephedradan

Date created: 1/12/2023

Purpose:

Details:

Description:

Notes:

IMPORTANT NOTES:

Explanation:

Tags:

Reference:

"""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import TYPE_CHECKING

from pacman.agent.heuristic_function import get_heuristic_function
from pacman.agent.search_problem import get_class_search_problem

from pacman.game.game_state import GameState
from pacman.game.layout import Layout
from pacman.agent.search.search import astar
from pacman.test_case.common import checkSolution
from pacman.test_case.test_case import TestCase

if TYPE_CHECKING:
    from pacman.grader import Grader


class HeuristicGrade(TestCase):

    def __init__(self, question, testDict):
        super(HeuristicGrade, self).__init__(question, testDict)
        self.layoutText = testDict['layout']
        self.layoutName = testDict['layoutName']
        self.searchProblemClassName = testDict['searchProblemClass']
        self.heuristicName = testDict['heuristic']
        self.basePoints = int(testDict['basePoints'])
        self.thresholds = [int(t) for t in testDict['gradingThresholds'].split()]

    def _setupProblem(self):
        lay = Layout([l.strip() for l in self.layoutText.split('\n')])
        gameState = GameState()
        gameState.initialize(lay, 0)
        # problemClass = getattr(searchAgents, self.searchProblemClassName)
        problemClass = get_class_search_problem(self.searchProblemClassName)

        problem = problemClass(gameState) # FIXME: JOSEPH FIX

        state = problem.getStartState()
        # heuristic = getattr(searchAgents, self.heuristicName)
        heuristic = get_heuristic_function(self.heuristicName)

        return problem, state, heuristic


    def execute(self, grader: Grader, dict_file_solution: Dict[str, Any]) -> bool:
        # search = moduleDict['search']
        # searchAgents = moduleDict['searchAgents']
        problem, _, heuristic = self._setupProblem()

        path = astar(problem, heuristic)

        expanded = problem._expanded

        if not checkSolution(problem, path):
            grader.addMessage('FAIL: %s' % self.path_file_test)
            grader.addMessage('\tReturned path is not a solution.')
            grader.addMessage('\tpath returned by astar: %s' % expanded)
            return False

        grader.addPoints(self.basePoints)
        points = 0
        for threshold in self.thresholds:
            if expanded <= threshold:
                points += 1
        grader.addPoints(points)
        if points >= len(self.thresholds):
            grader.addMessage('PASS: %s' % self.path_file_test)
        else:
            grader.addMessage('FAIL: %s' % self.path_file_test)
        grader.addMessage('\texpanded nodes: %s' % expanded)
        grader.addMessage('\tthresholds: %s' % self.thresholds)

        return True


    def writeSolution(self, filePath):
        handle = open(filePath, 'w')
        handle.write('# This is the solution file for %s.\n' % self.path_file_test)
        handle.write('# File intentionally blank.\n')
        handle.close()
        return True

