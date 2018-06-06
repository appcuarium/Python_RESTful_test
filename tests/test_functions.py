#!/usr/bin/env python
# -*- coding: utf-8 -*-
from unittest import TestCase
from main import calculate_distances
import pandas as pd
import numpy as np

test_data = [
    [
        [(52.516667, 13.388890), (51.507222, -0.1275), (55.75, 37.616667)],
        930.4536241898576,
        2500.543166926314,
        1680.302029758481,
        642.9160886404449,
    ],
]


def create_points(n):
    return pd.DataFrame({'Latitude': np.random.uniform(0.0, 90.0, n),
                         'Longitude': np.random.uniform(0.0, 180.0, n)})


track_points = create_points(25000)
test_points = create_points(400)


class TestFunctions(TestCase):
    def test_min_distance(self):
        for item in test_data:
            self.assertEqual(calculate_distances(item[0])['min'], item[1])

    def test_max_distance(self):
        for item in test_data:
            self.assertEqual(calculate_distances(item[0])['max'], item[2])

    def test_average_distance(self):
        for item in test_data:
            self.assertEqual(calculate_distances(item[0])['avg'], item[3])

    def test_std_deviation_distance(self):
        for item in test_data:
            self.assertEqual(calculate_distances(item[0])['std'], item[4])
