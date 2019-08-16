from decaptcha.fsm import State, StateMachine
from decaptcha.capture import capture
from decaptcha.humanclick import humanclick
from decaptcha.ocr import ocr
from decaptcha.objectdetection import *
from os import getcwd
from PIL import Image
from pyautogui import locate
from pyautogui import locateOnScreen
from pyscreeze import Box
import random
import time
from typing import Dict, List, Optional, Set, Tuple, Union


class GroundState(State):
    def imnotarobot(self) -> Tuple[int, int]:
        # Locate "I'm not a robot" button on screen
        imnotarobot = locateOnScreen(
            getcwd() + "/decaptcha/imnotarobot.png", confidence=0.7
        )
        # Click "I'm not a robot" button like a human
        left = int(imnotarobot.left + 0.10 * imnotarobot.width)
        top = int(imnotarobot.top - 0.10 * imnotarobot.height)
        right = int(imnotarobot.left + 0.75 * imnotarobot.width)
        bottom = int(imnotarobot.top + 0.90 * imnotarobot.height)
        return humanclick(left, top, right, bottom)

    def findbutton(self) -> "Box":
        # Attempt to see if recaptcha test exists on screen
        # try finding verify or skip button
        for target in ["skip.png", "verify.png", "next.png"]:
            try:
                button = locateOnScreen(
                    getcwd() + "/decaptcha/" + target, confidence=0.7
                )
                assert isinstance(button, tuple)
                return button
            except AssertionError:
                pass
        raise AttributeError("Failed to locate button")

    def refreshpuzzle(self, button: "Box") -> Tuple[int, int]:
        left = int(button.left) - 325 + int((button.width + button.width % 2) / 2)
        top = int(button.top) - 10 + int((button.height + button.height % 2) / 2)
        right = left + 20
        bottom = top + 20
        return humanclick(left, top, right, bottom)

    def savepuzzle(self, button: "Box", puzzlename: str = "puzzle.png") -> None:
        target_offset_top = (
            button.top - 430 + int((button.height + button.height % 2) / 2)
        )
        target_offset_left = (
            button.left - 344 + int((button.width + button.width % 2) / 2)
        )
        capture(target_offset_top, target_offset_left, 404, 410, puzzlename)
        capture(
            target_offset_top - 124, target_offset_left, 404, 122, "word" + puzzlename
        )

    def extractword(self, puzzlename: str = "greyinvert_wordpuzzle.png") -> str:
        # Attempt to extract word from last saved recaptcha puzzle
        word = ocr(puzzlename, 0, 0, 300, 122)
        try:
            assert isinstance(word, str)
        except:
            raise TypeError
        return word

    def isclassifiable(self, word: str) -> bool:
        for thing in objectlib():
            if thing in word:
                return True
        return False

    def verify(self, button: "Box") -> Tuple[int, int]:
        # Click verify
        left = int(button.left + 0.2 * button.width)
        top = int(button.top + 0.2 * button.height)
        right = int(button.left + 0.8 * button.width)
        bottom = int(button.top + 0.8 * button.height)
        return humanclick(left, top, right, bottom)

    def redundantclick(self, button: "Box") -> Tuple[int, int]:
        # Click arbitrary spot left of verify
        left = int(button.left - 1.2 * button.width)
        top = int(button.top - 0.1 * button.height)
        right = int(button.left - 0.2 * button.width)
        bottom = int(button.top + 1.0 * button.height)
        return humanclick(left, top, right, bottom)

    def extractartifacts(
        self, word: str, puzzlename: str = "puzzle.png"
    ) -> Dict[str, Tuple[int, int, int, int]]:
        """Find all artifacts that match word in last saved puzzle and save as images
        Return a dictionary of artifacts containing relative coordinates hashed by their filenames

        INPUT
        -----
        word : str

        puzzlename : str = "puzzle.png"
        """

        # Detect artifacts on-screen
        detections = objectdetection(word, puzzlename)  # type: List
        assert isinstance(detections, list)

        # Iterate through detections and return save img names and regions...
        result = dict()  # type: dict
        for thing in detections:

            try:
                # Crop images in puzzle contained within "box_points" & save to filename
                left = int(thing["box_points"][0])
                upper = int(thing["box_points"][1])
                right = int(thing["box_points"][2])
                lower = int(thing["box_points"][3])

                filename = "".join(["L", str(left), "T", str(upper), ".png"])

                img = Image.open(puzzlename)
                img_crop = img.crop((left, upper, right, lower))
                img_crop.save(filename)
                img_crop.close()
                img.close()
            except:
                pass
            else:
                result[filename] = thing["box_points"]

        return result

    def locateblacklist(
        self,
        cached_artifacts: Dict[str, Tuple[int, int, int, int]] = dict(),
        puzzlename: str = "puzzle.png",
    ) -> Set[Optional["Box"]]:
        """Locate any cached artifacts in puzzle and return a set of "Boxes" to be blacklisted.

        INPUT
        -----
        cached_artifacts : dict()
        puzzlename: str
        """

        # Check if cached artifacts is empty. If so, return empty set
        try:
            assert len(cached_artifacts) == 0
            return set()
        except:
            # Not empty, so iterate through and return their locations...
            result = set()  # type: set
            for cached_artifact in cached_artifacts:
                try:
                    img = locate(
                        "".join([getcwd(), "/", str(cached_artifact)]),
                        "".join([getcwd(), "/", str(puzzlename)]),
                        confidence=0.3,
                    )
                    assert hasattr(img, "left")
                except:
                    pass
                else:
                    # No exception thrown, so it's likely an area we want to blacklist
                    result.add(img)
                    # One result is enough
                    break
            return result

    def find4x4grid(self, puzzlename: str = "puzzle.png") -> Optional["Box"]:
        return locate(
            getcwd() + "/decaptcha/white4x4.png",
            getcwd() + "/" + puzzlename,
            confidence=0.5,
        )

    def iscollision(self, edge1: Tuple[int, int], edge2: Tuple[int, int]) -> bool:
        """Takes two parallel 1-D edges and returns if they overlap"""
        if (
            edge1[0] >= edge2[0]
            and edge1[0] <= edge2[1]
            or edge1[1] >= edge2[0]
            and edge1[1] <= edge2[1]
            or edge2[0] >= edge1[0]
            and edge2[0] <= edge1[1]
            or edge2[1] >= edge1[0]
            and edge2[1] <= edge1[1]
        ):
            return True
        else:
            return False

    def selectartifacts(
        self,
        button: "Box",
        artifacts: Dict[str, Tuple[int, int, int, int]],
        grid: "Box" = tuple(),
    ) -> None:
        """Click on all artifacts, relative to button location.

        If grid parameter specified, click on all grid cells occupied by any artifacts.

        INPUT
        -----
        cached_artifacts : dict()
        """

        # Compute coordinate references
        puzzle_top = (
            int(button.top) - 428 + int((button.height + button.height % 2) / 2)
        )
        puzzle_left = (
            int(button.left) - 342 + int((button.width + button.width % 2) / 2)
        )

        # Check for whether 4x4 grid was identified
        try:
            assert hasattr(grid, "left")

            # Constant parameters
            cell_width = 97
            click_margin = 10

            # Grid exists. Iterate through cells in 4x4 grid and click it if occupied by an artifact
            for cell in range(16):

                # Define cell as row & col no.
                row, col = int(abs(cell % 4 - cell) / 4), cell % 4

                # Calculate cell region based on grid location relative to puzzle
                cell_left = col * cell_width + grid.left + 6
                cell_top = row * cell_width + grid.top + 5
                cell_right = (col + 1) * cell_width + grid.left + 6
                cell_bottom = (row + 1) * cell_width + grid.top + 5

                # Determine whether cell region contains an artifact
                for artifact in artifacts.values():
                    try:
                        # Check if a collision occurs
                        assert (
                            # Collision in x axis
                            self.iscollision(  # type: ignore
                                tuple([artifact[0], artifact[2]]),
                                tuple([cell_left, cell_right]),
                            )
                            # Collision in y axis
                            and self.iscollision(  # type: ignore
                                tuple([artifact[1], artifact[3]]),
                                tuple([cell_top, cell_bottom]),
                            )
                        )
                    except:
                        # No collision here
                        pass
                    else:
                        # Artifact is contained within cell, so click region & proceed to next cell
                        left = cell_left + puzzle_left + click_margin
                        top = cell_top + puzzle_top + click_margin
                        right = cell_right + puzzle_left - click_margin
                        bottom = cell_bottom + puzzle_top - click_margin

                        clicked = humanclick(left, top, right, bottom)
                        print(clicked, time.time())
                        break

        # No grid specified. Click all artifacts relative to button
        except:
            try:
                for artifact in artifacts.values():
                    left = artifact[0] + puzzle_left
                    top = artifact[1] + puzzle_top
                    right = artifact[2] + puzzle_left
                    bottom = artifact[3] + puzzle_top

                    clicked = humanclick(left, top, right, bottom)
                    print(clicked, time.time())
            except:
                pass
