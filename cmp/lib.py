import copy
import pickle
import random
from random import randint
import os
import django
import numpy as np

from cmp.lib2 import calculate_est

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dipl.settings")
django.setup()

from cmp.models import Weights, GroupWeights

COUNT = 20

input_file_template = '../static/result/%s'


def cmp(weights, param='kfavg', group=-1):
    input_file = open(input_file_template % param, 'rb')
    data, name_groups, old_ranking, academic_performance = pickle.load(input_file)

    if group != -1:
        data.pop(group)
        name_groups.pop(group)
        old_ranking.pop(group)
        academic_performance.pop(group)
    new_ranking = calculate_est(data, weights)

    return old_ranking, new_ranking, [abs(old - new) for old, new in zip(old_ranking, new_ranking)], name_groups


def put_best(weights, sum, param='kfavg'):
    objects = Weights.objects.filter(type=param).order_by('-deviations_sum')
    if objects.count() < COUNT:
        Weights.objects.create(weights=' '.join(str(e) for e in weights), deviations_sum=sum, type=param)
    elif objects.first().deviations_sum > sum:
        objects.first().delete()
        Weights.objects.create(weights=' '.join(str(e) for e in weights), deviations_sum=sum, type=param)


def generate_random_weights(iter_count):
    random_weights = [[randint(1, 9) for i in range(45)] for i in range(iter_count)]
    for weights in random_weights:
        put_best(weights, sum(cmp(weights, param='c')[2]), param='c')


def fitness(set_weights, data, old_ranking):
    return [sum([abs(old - new) for old, new in zip(old_ranking, calculate_est(data, weights))]) for weights in
            set_weights]


def mating_pool(pop, fitness, num_parents):
    fitness, pop = np.array(fitness), np.array(pop)
    ind = np.argpartition(fitness, num_parents)[-num_parents:]
    ind = ind[np.argsort(fitness[ind])]
    return pop[ind]


def crossover(parents, offspring_size):
    offsprings = np.empty(offspring_size)
    crossover_point = int(offspring_size[1] / 2)

    for k in range(offspring_size[0]):
        parent1_idx = k % parents.shape[0]
        parent2_idx = (k + 1) % parents.shape[0]
        offsprings[k, 0:crossover_point] = parents[parent1_idx, 0:crossover_point]
        offsprings[k, crossover_point:] = parents[parent2_idx, crossover_point:]
    return offsprings


def mutation(offsprings):
    gene_index = random.randint(0, offsprings.shape[1] - 1)

    for off_index in range(offsprings.shape[0]):
        offsprings[off_index, gene_index] = random.randint(1, 9)
    return offsprings


def genetic_algoritm(param='avg'):
    input_file = open(input_file_template % param, 'rb')
    data, name_groups, old_ranking, academic_performance = pickle.load(input_file)
    num_weights = 45
    sol_per_pop = 8
    num_generations = 10
    num_parents = 5
    offspring_size = (2, num_weights)
    population = np.array([[randint(1, 9) for i in range(num_weights)] for i in range(sol_per_pop)])
    fitnesses = []
    for generation in range(num_generations):
        fitnesses = fitness(population, data, old_ranking)
        parents = mating_pool(population, fitnesses, num_parents)
        offsprings = crossover(parents, offspring_size)
        offspring_mutation = mutation(offsprings)
        population[0:parents.shape[0], :] = parents
        population[parents.shape[0]:, :] = offspring_mutation
    print(fitnesses)
    return population


genetic_algoritm(param='avg')
