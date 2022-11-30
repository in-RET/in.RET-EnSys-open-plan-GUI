# -*- coding: utf-8 -*-
"""
Created on Tue Nov 29 14:24:18 2022

@author: treinhardt01
"""

# from pyomo.opt import SolverFactory

from gurobipy import *

model = read("my_model.lp")
model.optimize()
