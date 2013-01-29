# -*- test-case-name: mamba.test.test_database -*-
# Copyright (c) 2012 Oscar Campos <oscar.campos@member.fsf.org>
# See LICENSE for more details

"""
.. module:: sqlite_adapter
    :platform: Unix, Windows
    :synopsis: SQLite adapter for create SQLite tables

.. moduleauthor:: Oscar Campos <oscar.campos@member.fsf.org>

"""

from storm import properties
from storm.expr import Undef
from storm.locals import create_database, Store

from mamba.utils import config


class SmallInt(properties.Int):
    """
    This class is a Storm extension of the MySQL and PostgreSQL numeric
    type used to store values in two bytes.

    Storm only uses the Int property type to store all kind of numeric data.
    This is a correct behaviour because Storm is a schemaless ORM but we
    need to know which exact weight we are going to use for a field because
    we generate the database using the model.
    """
    pass


class BigInt(properties.Int):
    """
    This class is a Storm extension of the MySQL and PostgreSQL numeric
    type used to store values in four bytes.

    Storm only uses the Int property type to store all kind of numeric data.
    This is a correct behaviour because Storm is a schemaless ORM but we
    need to know which exact weight we are going to use for a field because
    we generate the database using the model.
    """
    pass


class DoublePrecission(properties.Float):
    """
    This class is a Storm extension of the MySQL and PostgreSQL floating type
    used to store approximate values in eigth bytes.

    Storm only uses the Int property type to store all kind of numeric data.
    This is a correct behaviour because Storm is a schemaless ORM but we
    need to know which exact weight we are going to use for a field because
    we generate the database using the model.
    """
    pass


class CommonSQL:
    """I do nothing, my only purpse is serve as dummy object
    """

    def insert_data(self):
        """
        Return the SQL syntax needed to insert the data already present
        in the table.
        """

        store = Store(create_database(config.Database().uri))
        registers = []
        rows = store.find(self.model.__class__)
        fields = [
            r._detect_attr_name(self.model.__class__) for r in
            self.model._storm_columns.keys()
        ]
        for r in rows:
            tmp_row = {}
            for field in fields:
                tmp_row[field] = getattr(r, field)
                print type(tmp_row)
            registers.append(tmp_row)

        if self.__class__.__name__ == 'MySQL':
            commas = '`'
        else:
            commas = "'"

        query = ''
        for register in registers:
            query += ('INSERT INTO {}{}{} ({}) VALUES ({});\n'.format(
                commas,
                self.model.__storm_table__,
                commas,
                ', '.join(register.keys()),
                ', '.join([(
                    str(field) if type(field) is not unicode
                    else "'{}'".format(field))
                    for field in register.values()
                ])
            ))

        return query

    def _parse_float(self, column):
        """
        Parse an specific floating point type for MySQL/Postgres, for example:

            double precession

        :param column: the Storm properties column to parse
        :type column: :class:`storm.properties.Float`
        """

        if column.__class__.__name__ == 'Float':
            column_type = 'real'
        else:
            column_type = 'double precission'

        return column_type

    def _parse_unicode(self, column):
        """
        Parse an specific floating point type for MySQL/Postgres, for example:

            varchar(256)

        :param column: the Storm properties column to parse
        :type column: :class:`storm.properties.Unicode`
        """

        size = column._get_column(self.model.__class__).size

        return '{}{}'.format(
            'text' if size is Undef else 'varchar',
            '({})'.format(size) if size is not Undef else ''
        )

    def _null_allowed(self, column):
        """
        Parse the column to check if a column allows NULL values

        :param column: the Storm properties column to parse
        :type column: :class:`storm.properties.Property`
        """

        property_column = column._get_column(self.model.__class__)
        null_allowed = property_column.variable_factory()._allow_none

        return ' NOT NULL' if not null_allowed else ''

    def _default(self, column):
        """
        Get the default argument for a column (if any)

        :param column: the Storm properties column to parse
        :type column: :class:`storm.properties.Property`
        """

        property_column = column._get_column(self.model.__class__)
        variable = property_column.variable_factory()

        if variable._value is not Undef:
            return ' {}'.format(variable._value)

        return ''
