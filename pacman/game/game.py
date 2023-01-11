# game.py
# -------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
#
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

# game.py
# -------
# Licensing Information: Please do not distribute or publish solutions to this
# name_project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html
# from util import *

from __future__ import annotations

import sys
import time
import traceback
from typing import List
from typing import TYPE_CHECKING

from pacman.agent.agent import Agent
from pacman.game.game_state import GameState
from pacman.graphics.graphics_pacman import GraphicsPacman
from pacman.util import TimeoutFunction
from pacman.util import TimeoutFunctionException

if TYPE_CHECKING:
    from pacman.game.rules.game_rules_classic import ClassicGameRules

try:
    import boinc

    _BOINC_ENABLED = True
except:
    _BOINC_ENABLED = False


class Game:
    """
    The Game manages the control flow, soliciting actions from agents.
    """

    def __init__(self,
                 list_agent: List[Agent],
                 graphics_pacman: GraphicsPacman,  # FIXME: CAN BE NO GRAPHCIS OR ACUTAL GRAPHICS
                 rules: ClassicGameRules,
                 index_starting: int = 0,
                 bool_mute_agents: bool = False,
                 bool_catch_exceptions: bool = False):

        self.agentCrashed: bool = False
        self.list_agent: List[Agent] = list_agent
        self.graphics_pacman: GraphicsPacman = graphics_pacman
        self.rules: ClassicGameRules = rules
        self.index_starting: int = index_starting
        self.gameOver: bool = False
        self.bool_mute_agents: bool = bool_mute_agents
        self.bool_catch_exceptions = bool_catch_exceptions
        self.moveHistory: List = []
        self.totalAgentTimes: List[int] = [0 for agent in list_agent]
        self.totalAgentTimeWarnings: List[int] = [0 for agent in list_agent]
        self.agentTimeout: bool = False
        import io
        self.agentOutput = [io.StringIO() for agent in list_agent]
        print()

    def _get_progress(self) -> float:
        if self.gameOver:
            return 1.0
        else:
            return self.rules.getProgress(self)

    def _agentCrash(self, agentIndex, quiet=False):
        "Helper method for handling agent crashes"
        if not quiet:
            traceback.print_exc()
        self.gameOver = True
        self.agentCrashed = True
        self.rules.agentCrash(self, agentIndex)

    OLD_STDOUT = None
    OLD_STDERR = None

    def _mute(self, agent_index: int):
        # print(f"{self._mute.__name__}: self.bool_mute_agents {self.bool_mute_agents}")
        if not self.bool_mute_agents:
            return
        global OLD_STDOUT, OLD_STDERR
        OLD_STDOUT = sys.stdout
        OLD_STDERR = sys.stderr
        sys.stdout = self.agentOutput[agent_index]
        sys.stderr = self.agentOutput[agent_index]

        raise Exception("MUTE HAPPENED")

    def _unmute(self):
        # print(f"{self._unmute.__name__}: self.bool_mute_agents {self.bool_mute_agents}")

        if not self.bool_mute_agents:
            return
        global OLD_STDOUT, OLD_STDERR
        # Revert stdout/stderr to originals
        sys.stdout = OLD_STDOUT
        sys.stderr = OLD_STDERR

        raise Exception("UNMUTE HAPPENED")

    def run(self):
        """
        Main control loop for game play.
        """
        self.graphics_pacman.initialize(self.state.data)

        # print(self.state, type(self.state), "self.state", type(self.state.data))
        # print("FFFFF")

        self.numMoves = 0

        self.state: GameState

        # self.graphics_pacman.initialize(self.game_state.makeObservation(1).data)
        # inform learning agents of the game start
        for i, agent in enumerate(self.list_agent):

            # TODO: JOSEPH - THIS SHOULD TECHNICALLY NEVER HIT
            # if not agent:
            #
            #     self._mute(i)
            #
            #     # this is a null agent, meaning it failed to load
            #     # the other team wins
            #     print("Agent %d failed to load" % i, file=sys.stderr)
            #     self._unmute()
            #     self._agentCrash(i, quiet=True)
            #     return

            if ("registerInitialState" in dir(agent)):  # Basically hasattr without the raising exception
                print("registerInitialState IS HERE YO", dir(agent))
                self._mute(i)
                if self.bool_catch_exceptions:
                    try:
                        timed_func = TimeoutFunction(
                            agent.registerInitialState,
                            int(self.rules.getMaxStartupTime(i))
                        )
                        try:
                            time_start = time.time()
                            timed_func(self.state.get_deep_copy())
                            time_taken = time.time() - time_start
                            self.totalAgentTimes[i] += time_taken
                        except TimeoutFunctionException:
                            print("Agent %d ran out of time on startup!" %
                                  i, file=sys.stderr)
                            self._unmute()
                            self.agentTimeout = True
                            self._agentCrash(i, quiet=True)
                            return
                    except Exception as data:
                        self._agentCrash(i, quiet=False)
                        self._unmute()
                        return
                else:
                    agent.registerInitialState(self.state.get_deep_copy())
                # TODO: could this exceed the total time
                self._unmute()

        agentIndex = self.index_starting
        numAgents = len(self.list_agent)

        # MAIN GAME LOOP!!!!!!!!!!!!!!!!!
        while not self.gameOver:  # TODO: GAME LOOP IS RIGHT HERE
            # Fetch the next agent
            agent = self.list_agent[agentIndex]

            move_time = 0
            skip_action = False

            ##################################################

            # TODO: CODE IS IN ASSIGNMENT 3 WITH LEARNING
            # Generate an observation of the game_state
            if 'observationFunction' in dir(agent):
                self._mute(agentIndex)
                if self.bool_catch_exceptions:
                    try:
                        timed_func = TimeoutFunction(
                            agent.observationFunction,
                            int(self.rules.getMoveTimeout(agentIndex))
                        )

                        try:
                            time_start = time.time()
                            observation = timed_func(self.state.get_deep_copy())
                        except TimeoutFunctionException:
                            skip_action = True

                        move_time += time.time() - time_start
                        self._unmute()
                    except Exception as data:
                        self._agentCrash(agentIndex, quiet=False)
                        self._unmute()
                        return
                else:
                    observation = agent.observationFunction(self.state.get_deep_copy())
                self._unmute()
            else:
                observation = self.state.get_deep_copy()

            ##################################################

            # Solicit an action
            action = None
            self._mute(agentIndex)

            if self.bool_catch_exceptions:  # TODO: THIS CODE IS NECESSARY JOSEPH, IT IS FOR THE autograder.py
                # raise Exception("ERROR CALLED IN GAME")
                try:
                    timed_func = TimeoutFunction(
                        agent.getAction,
                        int(self.rules.getMoveTimeout(agentIndex)) - int(move_time)
                    )

                    try:
                        time_start = time.time()

                        if skip_action:  # TODO: DONT HAVE CONTROL OVER THIS JOSEPH
                            raise TimeoutFunctionException()

                        action = timed_func(observation)
                    except TimeoutFunctionException:
                        print("Agent %d timed out on a single move!" %
                              agentIndex, file=sys.stderr)
                        self.agentTimeout = True
                        self._agentCrash(agentIndex, quiet=True)
                        self._unmute()
                        return

                    move_time += time.time() - time_start

                    if move_time > self.rules.getMoveWarningTime(agentIndex):
                        self.totalAgentTimeWarnings[agentIndex] += 1
                        print("Agent %d took too long to make a move! This is warning %d" % (
                            agentIndex, self.totalAgentTimeWarnings[agentIndex]), file=sys.stderr)
                        if self.totalAgentTimeWarnings[agentIndex] > self.rules.getMaxTimeWarnings(agentIndex):
                            print("Agent %d exceeded the maximum number of warnings: %d" % (
                                agentIndex, self.totalAgentTimeWarnings[agentIndex]), file=sys.stderr)
                            self.agentTimeout = True
                            self._agentCrash(agentIndex, quiet=True)
                            self._unmute()
                            return

                    self.totalAgentTimes[agentIndex] += move_time
                    # print "Agent: %d, time: %f, total: %f" % (agentIndex, move_time, self.totalAgentTimes[agentIndex])
                    if self.totalAgentTimes[agentIndex] > self.rules.getMaxTotalTime(agentIndex):
                        print("Agent %d ran out of time! (time: %1.2f)" % (
                            agentIndex, self.totalAgentTimes[agentIndex]), file=sys.stderr)
                        self.agentTimeout = True
                        self._agentCrash(agentIndex, quiet=True)
                        self._unmute()
                        return
                    self._unmute()
                except Exception as data:
                    self._agentCrash(agentIndex)
                    self._unmute()
                    return
            else:
                action = agent.getAction(observation)

            ##################################################

            self._unmute()

            self.moveHistory.append((agentIndex, action))

            # Execute the action
            if self.bool_catch_exceptions:
                try:
                    self.state = self.state.generateSuccessor(agentIndex, action)
                except Exception as data:
                    # raise Exception("JOSEPH WTF")

                    self._mute(agentIndex)
                    self._agentCrash(agentIndex)
                    self._unmute()
                    return
            else:
                self.state = self.state.generateSuccessor(agentIndex, action)

            # Change the graphics_pacman
            self.graphics_pacman.update(self.state.data)

            ###idx = agentIndex - agentIndex % 2 + 1
            ###self.graphics_pacman.update( self.game_state.makeObservation(idx).data )

            # Allow for game specific conditions (winning, losing, etc.)
            self.rules.process(self.state, self)
            # Track progress
            if agentIndex == numAgents + 1:
                self.numMoves += 1
            # Next agent
            agentIndex = (agentIndex + 1) % numAgents

            if _BOINC_ENABLED:
                boinc.set_fraction_done(self._get_progress())

        #########################################################
        #########################################################

        # inform a learning agent of the game result
        for agentIndex, agent in enumerate(self.list_agent):
            if "final" in dir(agent):
                try:
                    self._mute(agentIndex)
                    agent.final(self.state)
                    self._unmute()
                except Exception as data:
                    if not self.bool_catch_exceptions:
                        raise
                    self._agentCrash(agentIndex)
                    self._unmute()
                    return
        self.graphics_pacman.finish()
