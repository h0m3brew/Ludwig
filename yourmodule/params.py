"""
use only dictionaries to store parameters.
ludwigcluster works on dictionaries and any custom class would force potentially unwanted logic on user.
using non-standard classes here would also make it harder for user to understand.
any custom classes for parameters should be implemented by user in main job function only.
keep interface between user and ludwigcluster as simple as possible
"""

param2requests = {'learning_rate': [0.1, 0.2, 0.3]}


param2default = {'learning_rate': 0.1,
                 'num_epochs': 500}