from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Binary, Integer
from pymoo.core.mixed import MixedVariableGA
from pymoo.optimize import minimize
import numpy as np
import random

class MixedVariableProblem(ElementwiseProblem):

    def __init__(self, n_couples=24, **kwargs):
        variables = {}
        for j in range(n_couples):
            variables[f"b{j}"] = Binary()
            variables[f"i{j}"] = Integer(bounds=(0, 100))
        super().__init__(vars=variables, n_obj=1, **kwargs)

    def _evaluate(self, X, out, *args, **kwargs):
        # Your evaluation logic here
        # Cosa dobbiamo fare?
        # Ora per ora
        sum = 0
        for j in range(24):
            sum = sum + X[f"i{j}"]
            print(X[f"i{j}"])
        out["F"] = sum



problem = MixedVariableProblem()

# Set the population size to 1
pop_size = 100
algorithm = MixedVariableGA(pop_size)

res = minimize(problem,
               algorithm,
               termination=('n_evals', 2),
               seed=random.randint(0, 99999),
               verbose=False)

print("Best solution found: \nX = %s\nF = %s" % (res.X, res.F))
