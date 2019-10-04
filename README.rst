====
FRED
====

This is the official Python implementation of the FRED format. This module
passes the FRED test suite and aims to the a reference implementation for dynamic
languages and a testbed for new features in FRED Schema format and other related
technologies.

.. warning::

    FRED is not stable yet. We want to figure out all the dark corners of the
    language before declaring it an official release. There will be **no** bugfix
    release after FRED 1.0, which will be the **only** official version of the FRED format.
    Once the official spec is published, which may take some time, all bugs will
    become features and the language will be crystallized for eternity.

    Other related technologies such as FRED Schema and recommendations for the
    creation of FRED documents and parsing libraries may evolve. Those are not
    part of the language spec.


Installation
============

To install the latest release on PyPI, run::

    $ pip install fred

Or use the development version at github::

    $ git clone https://github.com/fred-format/fred-python.git
    $ cd fred-python
    $ python setup.py install


What is FRED?
=============

FRED is a data representation format that extends JSON with new syntax and data
types. FRED is simple, extensible and backwards compatible with JSON. The main
extension to JSON type system is the introduction of tagging as a unified way
to extend the existing types and attach metadata to any object or value.

The example displays the use of tags and a few syntactic sugar introduced by the
format

```
;; A simple person record
Person {
    name: "Alan Turing"
    birthday: 1900-01-01
    awards: [
        Award (when=232342) "dfsfs"
        Award (when=123122) "djfodjos
    ]
}
```

Comparing it to JSON, there are a few notable differences:

* Any value can be tagged and associated with optional metadata.
* It introduces a few extra atomic types: datetime, symbols and byte strings.
* It accepts LISP-like line comments using the ";" delimiter.
* Keys do not require quotes.
* Commas are treated as whitespace, which makes them optional separators.
* It is a superset of JSON, hence quoting keys and adding commas is also accepted.

We refer to the tutorial for a more information. Language lawyers will probably
want to see the `working specification`_ for even more details.


Usage and quick API overview
============================

First,

>>> import fred

FRED is inspired by JSON, and similarly, the API of this module was designed to
mirror Python's native :mod:`json` module. It implements a familiar interface
using func:`load(s)`, and :func:`dump(s)` functions.

>>> fred.loads('Fred "Hello, Fred!"')
Tag('Fred', 'Hello, Fred!')

#TODO: few options

FRED types are mapped to native Python ones when it makes sense (e.g., FRED byte
strings become Python's bytes, FRED dates are mapped into classes of the datetime
module, and so on). However, there are a two FRED constructs that have no Python
correspondence: symbols and tag elements. They are implemented by the new
:cls:`fred.Symbol` and :cls:`fred.Tag` classes. You can use them
directly to construct your own FRED data structures.

>>> data = fred.Tag('Person', {'name': 'Alan Turing'}, id=fred.Symbol('id'))
>>> fred.dump(data)  # The default out file is sys.stdout
Person (id=$id) {name: Alan Turing}


Handling tags
=============


Fred schema
===========

FRED schema declares additional validity rules and simple normalization
procedures to FRED documents. #...

FRED validating parsers are initialized with the ``fred.schema`` function.

>>> person_parser = fred.schema("""
Schema/Person (id="my-org/person") [
    Person {
        first-name: (String)
        last-name: (String?)
        birthday: (Date?)
    }
]
""")

These objects have the familiar load(s)/dump(s) methods.

>>> person_parser.loads('Person {first-name: "John", last-name: "Lennon"}')

Notice the parser now rejects valid FRED documents that violate the schema.

>>> person_parser.loads('Person {name: "John Lennon"}')