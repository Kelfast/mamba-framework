
# Copyright (c) 2012 - Oscar Campos <oscar.campos@member.fsf.org>
# Ses LICENSE for more details

"""
Tests for mamba.enterprise.database
"""

from storm.locals import Store
from twisted.trial import unittest
from twisted.python.threadpool import ThreadPool
from doublex import Spy, assert_that, called, ANY_ARG

from mamba.utils import config
from mamba.enterprise import Database
from mamba.application.model import ModelManager
from mamba.enterprise.database import AdapterFactory


class DatabaseTest(unittest.TestCase):

    def setUp(self):
        config.Database().load(
            '../mamba/test/application/config/database.json'
        )
        self.database = Database(self.get_pool())

    def tearDown(self):
        self.database.pool.stop()

    def get_pool(self):

        with Spy() as pool:
            pool.start(ANY_ARG)
            pool.stop(ANY_ARG)

        return pool

    def test_database_initial_name_is_database_pool(self):

        database = Database()
        self.assertEqual(database.pool.name, 'DatabasePool')

    def test_databse_initial_pool_size_is_five_and_twenty_five(self):

        database = Database()
        self.assertEqual(database.pool.min, 5)
        self.assertEqual(database.pool.max, 20)

    def test_database_initial_pool_size_min_negative_fail_assertion(self):

        self.assertRaises(AssertionError, ThreadPool, -1)

    def test_database_initial_size_min_greater_than_max_fail_assertion(self):

        self.assertRaises(AssertionError, ThreadPool, 30)

    def test_database_start(self):

        self.assertFalse(self.database.started)
        self.database.start()

        assert_that(self.database.pool.start, called().times(1))
        self.assertTrue(self.database.started)

    def test_database_start_returns_if_is_already_started(self):

        self.assertFalse(self.database.started)

        self.database.start()
        self.database.start()

        assert_that(self.database.pool.start, called().times(1))
        self.assertTrue(self.database.started)

    def test_database_stop(self):

        self.assertFalse(self.database.started)
        self.database.start()
        assert_that(self.database.pool.start, called().times(1))
        self.assertTrue(self.database.started)

        self.database.stop()
        assert_that(self.database.pool.stop, called().times(1))
        self.assertFalse(self.database.started)

    def test_database_stop_returns_if_is_already_stopped(self):

        self.assertFalse(self.database.started)
        self.database.start()
        assert_that(self.database.pool.start, called().times(1))
        self.assertTrue(self.database.started)

        self.database.stop()
        self.database.stop()
        assert_that(self.database.pool.stop, called().times(1))
        self.assertFalse(self.database.started)

    def test_database_adjust_size(self):

        self.database.pool = ThreadPool(0, 10)

        self.database.adjust_poolsize(4, 20)
        self.assertEqual(self.database.pool.min, 4)
        self.assertEqual(self.database.pool.max, 20)

    def test_database_adjust_size_min_negative_fail_assertion(self):

        self.database.pool = ThreadPool(0, 10)
        self.assertRaises(AssertionError, self.database.adjust_poolsize, -1)

    def test_database_adjust_size_min_greater_than_max_fail_assertion(self):

        self.database.pool = ThreadPool(0, 10)
        self.assertRaises(AssertionError, self.database.adjust_poolsize, 20)

    def test_database_store(self):
        store = self.database.store()
        self.assertIsInstance(store, Store)

    def test_database_backend(self):
        self.assertEqual(self.database.backend(), 'sqlite')

    def test_database_dump(self):
        import sys
        sys.path.append('../mamba/test/dummy_app')
        mgr = ModelManager()
        self.addCleanup(mgr.notifier.loseConnection)

        from mamba import Model
        from mamba.test.test_model import DummyThreadPool, DatabaseModuleError
        try:
            threadpool = DummyThreadPool()
            database = Database(threadpool)
            Model.database = database

            store = database.store()
            store.execute(
                'CREATE TABLE IF NOT EXISTS `dummy` ('
                '    id INTEGER PRIMARY KEY, name TEXT'
                ')'
            )
            store.commit()
        except DatabaseModuleError, error:
            raise unittest.SkipTest(error)

        mgr.load('../mamba/test/dummy_app/application/model/dummy.py')
        mgr.load('../mamba/test/dummy_app/application/model/stubing.py')
        sql = self.database.dump(mgr)
        self.assertTrue('CREATE TABLE IF NOT EXISTS dummy (\n' in sql)
        self.assertTrue('  name VARCHAR NOT NULL,\n' in sql)
        self.assertTrue('  id INTEGER,\n' in sql)
        self.assertTrue('  PRIMARY KEY(id)\n);\n\n' in sql)
        self.assertTrue('CREATE TABLE IF NOT EXISTS stubing (\n' in sql)
        self.assertTrue('  id INTEGER,\n' in sql)
        self.assertTrue('  name VARCHAR NOT NULL,\n' in sql)
        self.assertTrue('  PRIMARY KEY(id)\n);\n' in sql)

        self.flushLoggedErrors()
        self.database.store().reset()


class AdapterFactoryTest(unittest.TestCase):

    def get_adapter_for_scheme(self, scheme):
        if scheme == 'sqlite':
            from mamba.enterprise.sqlite import SQLite
            return AdapterFactory('sqlite', None).produce(), SQLite
        elif scheme == 'mysql':
            from mamba.enterprise.mysql import MySQL
            return AdapterFactory('mysql', None).produce(), MySQL
        else:
            from mamba.enterprise.postgres import PostgreSQL
            return AdapterFactory('postgres', None).produce(), PostgreSQL

    def test_sqlite_adapter(self):
        factory, instance = self.get_adapter_for_scheme('sqlite')
        self.assertIsInstance(factory, instance)

    def test_mysql_adapter(self):
        factory, instance = self.get_adapter_for_scheme('mysql')
        self.assertIsInstance(factory, instance)

    def test_postgres_adapter(self):
        factory, instance = self.get_adapter_for_scheme('postgres')
        self.assertIsInstance(factory, instance)
