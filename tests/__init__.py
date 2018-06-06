#!/usr/bin/env python
# -*- coding: utf-8 -*-
import base64
import json
from unittest import TestCase

from main import app


class BaseTest(TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['MONGO_DBNAME'] = 'restdb'
        app.config['MONGO_URI'] = 'mongodb://localhost:27017/prtdb'
        cls.api = app.test_client()
        cls.app_context = app.app_context()

    def setUp(self):
        self.username = 'testuser1'
        self.password = 'testP4ssword'
        self.user = None

    def tearDown(self):
        pass

    def register_user(self, username, password):
        self.user = self.api.post(
            '/register',
            data=json.dumps(
                dict(
                    username=username,
                    password=password,
                )
            ), content_type='application/json'
        )

        return self.user

    def base_test_user(self):
        return self.register_user(self.username, self.password, )

    def login_user(self):
        self.user = self.api.post(
            '/login',
            data=json.dumps(
                dict(
                    username=self.username,
                    password=self.password,
                )
            ), content_type='application/json'
        )

        return self.user

    def set_auth_headers(self):
        return {
            'Authorization': 'Basic ' + base64.b64encode(
                bytes(self.username + ":" + self.password, 'ascii')).decode(
                'ascii')
        }
