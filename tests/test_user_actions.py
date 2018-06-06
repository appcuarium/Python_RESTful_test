#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
from uuid import uuid4

from tests import BaseTest


class TestUserLogin(BaseTest):
    def setUp(self):
        super(TestUserLogin, self).setUp()

    def test_login(self):
        # Create test user if not exists
        self.base_test_user()

        # Login test user
        login = self.login_user()

        response = json.loads(login.data)

        self.assertEqual(login.status_code, 200)
        self.assertFalse(len(response['errors']))

    def test_register_new_user(self):
        username = str(uuid4())
        register = self.register_user(username, self.password)

        response = json.loads(register.data)

        self.assertEqual(len(response['errors']), 0)
        self.assertEqual(response['results']['username'], username)

    def test_get_all_users(self):
        # Create test user if not exists
        self.base_test_user()

        # Login test user
        self.login_user()

        users = self.api.get('/prt/api/v1.0/users',
                             headers=self.set_auth_headers(),
                             content_type='application/json')

        response = json.loads(users.data)

        self.assertEqual(len(response['errors']), 0)
        self.assertTrue(len(response['results']) > 0)

    def test_get_users_by_id(self):
        # Create test user if not exists
        self.base_test_user()

        # Login test user
        self.login_user()

        user_data = json.loads(self.user.data)

        query = '/prt/api/v1.0/users/{}'.format(user_data['results'][0]['id'])
        users = self.api.get(query,
                             headers=self.set_auth_headers(),
                             content_type='application/json')

        response = json.loads(users.data)

        self.assertEqual(len(response['errors']), 0)
        self.assertEqual(response['results']['username'],
                         user_data['results'][0]['username'])

    def test_create_new_user(self):
        # Create test user if not exists
        self.base_test_user()

        # Login test user
        self.login_user()

        username = str(uuid4())

        new_user = self.api.post(
            '/prt/api/v1.0/users',
            data=json.dumps(
                dict(
                    username=username,
                    password=self.password,
                )
            ),
            headers=self.set_auth_headers(),
            content_type='application/json'
        )

        response = json.loads(new_user.data)

        self.assertEqual(len(response['errors']), 0)
        self.assertEqual(response['results']['username'], username)

    def test_update_user_data(self):
        # Create test user if not exists
        self.base_test_user()

        # Login test user
        self.login_user()

        user_data = json.loads(self.user.data)

        query = '/prt/api/v1.0/users/{}'.format(user_data['results'][0]['id'])
        first_name = last_name = str(uuid4())
        update_user = self.api.put(
            query,
            data=json.dumps(
                dict(
                    name=dict(
                        first_name=first_name,
                        last_name=last_name,
                    ),
                    location=dict(
                        type='Point',
                        coordinates=[-180, 90]
                    )
                ),
            ),
            headers=self.set_auth_headers(),
            content_type='application/json'
        )

        response = json.loads(update_user.data)

        self.assertEqual(len(response['errors']), 0)
        self.assertTrue(response['updated'])
        self.assertEqual(response['results']['name']['first_name'], first_name)
        self.assertEqual(response['results']['name']['last_name'], last_name)

    def test_delete_user(self):
        # Create test user if not exists
        self.base_test_user()

        # Login test user
        self.login_user()

        username = str(uuid4())

        new_user = self.api.post(
            '/prt/api/v1.0/users',
            data=json.dumps(
                dict(
                    username=username,
                    password=self.password,
                )
            ),
            headers=self.set_auth_headers(),
            content_type='application/json'
        )

        response = json.loads(new_user.data)

        query = '/prt/api/v1.0/users/{}'.format(response['results']['id'])

        delete_user = self.api.delete(
            query,
            headers=self.set_auth_headers()
        )

        response = json.loads(delete_user.data)

        self.assertEqual(len(response['errors']), 0)
        self.assertTrue(response['updated'])

    def test_calculate_distance_between_users(self):
        # Create test user if not exists
        self.base_test_user()

        # Login test user
        self.login_user()

        username = str(uuid4())

        new_user = self.api.post(
            '/prt/api/v1.0/users',
            data=json.dumps(
                dict(
                    username=username,
                    password=self.password,
                )
            ),
            headers=self.set_auth_headers(),
            content_type='application/json'
        )

        new_user_response = json.loads(new_user.data)
        query = '/prt/api/v1.0/users/{}'.format(
            new_user_response['results']['id'])

        self.api.put(
            query,
            data=json.dumps(
                dict(
                    location=dict(
                        type='Point',
                        coordinates=[
                            random.uniform(0.0, 90.0),
                            random.uniform(0.0, 180.0),
                        ]
                    )
                ),
            ),
            headers=self.set_auth_headers(),
            content_type='application/json'
        )

        get_distance = self.api.get(
            '/prt/api/v1.0/distances',
            headers=self.set_auth_headers(),
            content_type='application/json'
        )

        response = json.loads(get_distance.data)

        self.assertEqual(len(response['errors']), 0)
        self.assertTrue(response['results']['min'] > 0)
        self.assertTrue(response['results']['max'] > 0)
        self.assertTrue(response['results']['avg'] > 0)
        self.assertTrue(response['results']['std'] > 0)
