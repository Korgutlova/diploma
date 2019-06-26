import pickle
import random
from random import randint
import os
import django
import numpy as np

from cmp.lib2 import calculate_estimations

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dipl.settings")
django.setup()

input_file_template = './static/cmp_results/2%s'

output_file_template = './static/cmp_results/2weights-%s'


def cmp(weights, param='avg'):
    input_file = open(input_file_template % param, 'rb')
    data, name_groups, old_ranking, academic_performance = pickle.load(input_file)

    new_ranking = calculate_estimations(data, weights)

    return old_ranking, new_ranking, [abs(old - new) for old, new in zip(old_ranking, new_ranking)], range(1, len(
        new_ranking) + 1)


def fitness_function(set_weights, param_values, expert_estimations):
    return [sum([abs(expert_est - automatic_est) for expert_est, automatic_est in
                 zip(expert_estimations, calculate_estimations(param_values, weights))]) for weights in
            set_weights]


def mating_pool(pop, fitness, num_parents):
    fitness, pop = np.array(fitness), np.array(pop)
    ind = np.argpartition(fitness, num_parents)[-num_parents:]
    ind = ind[np.argsort(fitness[ind])]
    return pop[ind]


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
        if calculate_estimations(data, list(offsprings[off_index, :])) > calculate_estimations(data, offspring_values):
            offsprings[off_index, :] = offspring_values
    return offsprings


def genetic_algorithm(param='avg'):
    input_file = open(input_file_template % param, 'rb')
    data, name_groups, old_ranking, academic_performance = pickle.load(input_file)
    num_weights = 45
    num_generations = 1000
    num_parents = 50

    offspring_size = (num_parents * 2, num_weights)
    sol_per_pop = int(offspring_size[0]) + num_parents

    population = np.array([[randint(1, 9) for i in range(num_weights)] for i in range(sol_per_pop)])

    fitnesses = []
    for generation in range(num_generations):
        fitnesses = fitness_function(population, data, old_ranking)
        parents = mating_pool(population, fitnesses, num_parents)
        offsprings = crossover(parents, offspring_size)
        offspring_mutation = mutation(offsprings, data)
        population[0:parents.shape[0], :] = parents
        population[parents.shape[0]:, :] = offspring_mutation
    min_fitness_value_index = fitnesses.index(min(fitnesses))
    print(fitnesses)
    file = open(output_file_template % param, 'wb')
    pickle.dump(' '.join(str(weight) for weight in population[min_fitness_value_index]), file)

    return population, fitnesses


