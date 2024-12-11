import sys
import pprint

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        #return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        removables = []
        for var in self.domains:
            for word in self.domains[var]:
                if var.length != len(word):
                    removables.append([var, word])
        for i in range(0, len(removables)):
            self.domains[removables[i][0]].remove(removables[i][1])


    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """

        overlap = self.is_overlap_between_x_and_y(x, y)
        if overlap == None:
            return False

        revised = False
        # for x in X.domain:
        #   if no y in Y.domain satisfies constraint for (X,Y):
        removables = []
        for word_x in self.domains[x]:
            contraint_satisfied = False
            character_at_intersection_x = word_x[overlap[0]]
            for word_y in self.domains[y]:
                character_at_intersection_y = word_y[overlap[1]]
                if character_at_intersection_x == character_at_intersection_y:
                    contraint_satisfied = True
            if not contraint_satisfied:
                removables.append(word_x)
                revised = True
        for i in range(0, len(removables)):
            self.domains[x].remove(removables[i])

        return revised


    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs == None:
            arcs = self.initialize_arcs([])

        while len(arcs) != 0:
            arc = arcs.pop(0)
            arc_x = arc[0]
            arc_y = arc[1]
            if self.revise(arc_x, arc_y):
                if len(self.domains[arc_x]) == 0:
                    return False
                for neighbor in self.crossword.neighbors(arc_x):
                    if neighbor.i != arc_y.i and neighbor.j != arc_y.j:
                        arcs.append((neighbor, arc_x))

        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        complete = True
        for domain in self.domains:
            if not domain in assignment:
                complete = False
        return complete

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        raise NotImplementedError

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        raise NotImplementedError

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        raise NotImplementedError

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        raise NotImplementedError

    def is_overlap_between_x_and_y(self, x, y):
        '''
        Returns the ith and jth coordinates of the words where they intersect
        '''
        overlaps = self.crossword.overlaps
        for overlap in overlaps:
            n_elements = 0
            count = 0
            for element in overlap:
                if element == x and count == 0:
                    n_elements += 1
                if element == y and count == 1:
                    n_elements += 1
                if n_elements == 2:
                    return overlaps[overlap]
                count += 1
        return None    


    def initialize_arcs(self, arcs):
        # Intialize empty arcs array
        overlaps = self.crossword.overlaps
        for overlap in overlaps:
            n_elements = 0
            count = 0
            for element in overlap:
                if n_elements == 0:
                    x = element
                if n_elements == 1:
                    y = element
                n_elements += 1
            if overlaps[(x, y)] != None:
                arcs.append((x, y))
        return arcs


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)

    # DEVELOP AND TEST THE REVISE FUNCTION
    # creator.revise(Variable(2, 1, 'down', 5), Variable(2, 1, 'across', 12))
    # return

    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
