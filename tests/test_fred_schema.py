from datetime import date

import pytest

from fred import loads, Tag
from fred.schema import parse_schema, schema
# ------------------------------------------------------------------------------
# Fixtures
from fred.schema.validators import make_validator


@pytest.fixture
def schema_src():
    return """
    Schema/Person (id="tests") [
        Person {
            first-name: (String)
            last-name: (String?)
            birthday: (Date?)
        }
    ]
    """


@pytest.fixture
def person_decl():
    return Tag('Person', {
        'first-name': Tag('String'),
        'last-name': Tag('String?'),
        'birthday': Tag('Date?'),
    })


# ------------------------------------------------------------------------------
# Test classes

class TestFredSchemaValidation:
    def test_can_load_schema_example(self, schema_src, person_decl):
        fred: Tag = loads(schema_src)
        parsed = parse_schema(fred)
        assert parsed.id == 'tests'
        assert parsed.exported == ['Person']
        assert parsed.declarations == {'Person': person_decl}


class TestFredMakeValidatorFunction:
    def test_make_simple_validator(self):
        validator = make_validator(Tag('Foo', Tag('String')), {})
        assert validator(None, Tag('Foo', 'bar')) == Tag('Foo', 'bar')


class TestFredSchemaParser:
    def test_happy_validating_parsing(self, schema_src):
        person = schema(schema_src)

        # Happy stories
        assert person.loads('Person {first-name: "Joe"}') == \
               Tag('Person', {'first-name': 'Joe', 'last-name': None, 'birthday': None})
        assert person.loads('Person {first-name: "Joe", last-name: "Smith"}') == \
               Tag('Person', {'first-name': 'Joe', 'last-name': 'Smith', 'birthday': None})
        assert person.loads('Person {first-name: "Joe", birthday: 1970-01-01}') == \
               Tag('Person', {'first-name': 'Joe', 'birthday': date(1970, 1, 1), 'last-name': None})
        assert person.loads('Person {first-name: "Joe", last-name: "Smith", birthday: 1970-01-01}') == \
               Tag('Person', {'first-name': 'Joe', 'last-name': 'Smith', 'birthday': date(1970, 1, 1)})
        assert person.loads('Person {first-name: "Joe", last-name: "Smith", birthday: null}') == \
               Tag('Person', {'first-name': 'Joe', 'last-name': 'Smith', 'birthday': None})

    def test_validating_parsing_errors(self, schema_src):
        person = schema(schema_src)

        # Unhappy stories
        with pytest.raises(TypeError) as e:
            person.loads('Person {first-name: null}')
            print(e)
