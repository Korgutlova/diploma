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

input_file_template = './static/result/%s'


def smart_gen():
    const_act = [0, 5, 10, 39, 40]
    d1_part = [(1, 4), (6, 9), (11, 12), (13, 14), (35, 38), (41, 44)]
    olimp = [(15, 18, 5), (19, 22, 6), (23, 26, 7), (27, 30, 8), (31, 34, 4)]
    coef = {}
    for ind in const_act:
        coef[ind] = random.randint(1, 9)
    for ind_st, ind_end in d1_part:
        ind = ind_end
        est = random.randint(4, 9)
        while ind >= ind_st:
            coef[ind] = est
            ind -= 1
            est -= 1
    for ind_st, ind_end, est_st in olimp:
        ind = ind_end
        est = est_st
        while ind >= ind_st:
            coef[ind] = est
            ind -= 1
            est -= 1
    coef = dict(sorted(coef.items(), key=lambda item: item[0]))
    return list(coef.values())


def cmp(weights, param='kfavg', group=-1):
    input_file = open(input_file_template % param, 'rb')
    data, name_groups, old_ranking, academic_performance = pickle.load(input_file)

    if group != -1:
        data.pop(group)
        name_groups.pop(group)
        old_ranking.pop(group)
        academic_performance.pop(group)
    new_ranking = calculate_est(data, weights)

    return old_ranking, new_ranking, [abs(old - new) for old, new in zip(old_ranking, new_ranking)], range(1,16)


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


def best_weights(pop, fitness, num_best):
    fitness, pop = np.array(fitness), np.array(pop)
    ind = np.argpartition(fitness, num_best)[-num_best:]
    ind = ind[np.argsort(fitness[ind])]
    return list(pop[ind]), list(fitness[ind])


def crossover(parents, offspring_size):
    offsprings = np.empty(offspring_size)
    crossover_point = int(offspring_size[1] / 2)
    k = 0
    p = 0
    while k < int(offspring_size[0]):
        parent1_idx = p % parents.shape[0]
        parent2_idx = (p + 1) % parents.shape[0]
        offsprings[k, 0:crossover_point] = parents[parent1_idx, 0:crossover_point]
        offsprings[k + 1, 0:crossover_point] = parents[parent2_idx, 0:crossover_point]

        offsprings[k, crossover_point:] = parents[parent2_idx, crossover_point:]
        offsprings[k + 1, crossover_point:] = parents[parent1_idx, crossover_point:]
        k += 2
        p += 1
    return offsprings


def mutation(offsprings, data):
    gene_index = random.randint(0, offsprings.shape[1] - 1)

    for off_index in range(offsprings.shape[0]):
        offspring_values = list(offsprings[off_index, :])
        offspring_values[gene_index] = random.randint(1, 9)
        if calculate_est(data, list(offsprings[off_index, :])) > calculate_est(data, offspring_values):
            offsprings[off_index, :] = offspring_values
    return offsprings


def genetic_algoritm(param='avg'):
    input_file = open(input_file_template % param, 'rb')
    data, name_groups, old_ranking, academic_performance = pickle.load(input_file)
    num_weights = 45
    num_generations = 1000
    num_parents = 50

    offspring_size = (num_parents * 2, num_weights)
    sol_per_pop = int(offspring_size[0]) + num_parents

    population = np.array([[randint(1, 9) for i in range(num_weights)] for i in range(sol_per_pop)])

    # population = np.array([smart_gen() for i in range(sol_per_pop)])

    fitnesses = []
    for generation in range(num_generations):
        fitnesses = fitness(population, data, old_ranking)
        parents = mating_pool(population, fitnesses, num_parents)
        offsprings = crossover(parents, offspring_size)
        offspring_mutation = mutation(offsprings, data)
        population[0:parents.shape[0], :] = parents
        population[parents.shape[0]:, :] = offspring_mutation
    weights, fits = best_weights(population, fitnesses, 20)
    print(weights)
    print(fits)
    for b_w, fit in zip(weights, fits):
        Weights.objects.create(weights=' '.join(str(e) for e in b_w), deviations_sum=fit, type=param, ga=True)
    return population


# print(mating_pool([3, 7, 2, 4, 1], [80, 50, 5, 10, 40], 2))

# print(smart_gen())

# for param in ['avg', 'kfavg', 'c', 'kf']:
#     genetic_algoritm(param)
