.. meta::
   :description: Find the packaged JSON Schema, check blocks with it in Python or another language, and know what it leaves out

.. py:currentmodule:: s_layer_semantic_formats

.. _howto-use-the-json-schema:

Use the JSON Schema in another tool
===================================

The package ships a JSON Schema (draft 2020-12) for the ``s_layer`` block, generated from
the same models that :py:func:`validate_block` uses. Use this guide to check block shape in a
tool that cannot call the Python models: a linter, a service in another language, or a
generic JSON Schema validator.

Before you start
----------------

- Install the package: ``pip install s-layer-semantic-formats``. The examples in Python also
  use ``jsonschema``: ``pip install jsonschema``.
- The schema describes one block, the value of ``config.meta.s_layer``. It does not describe
  a whole dbt property file.

Find the schema file
--------------------

:py:data:`SCHEMA_PATH` is the path of ``s_layer.schema.json`` inside the installed package,
and :py:func:`load_schema` reads it:

.. code-block:: python

   from s_layer_semantic_formats import SCHEMA_PATH, load_schema

   schema = load_schema()

   print(SCHEMA_PATH.name)
   print(schema["$schema"])
   print(schema["title"])

.. code-block:: text

   s_layer.schema.json
   https://json-schema.org/draft/2020-12/schema
   S-LAYER semantic format block

The file ships with each release, so its contents change only when you upgrade the package.

Check a block with jsonschema
-----------------------------

Build a :py:class:`~jsonschema.validators.Draft202012Validator` from the schema. Use
:py:func:`jsonschema.exceptions.best_match` to pick the most useful error:

.. code-block:: python

   from jsonschema import Draft202012Validator
   from jsonschema.exceptions import best_match

   from s_layer_semantic_formats import load_schema

   validator = Draft202012Validator(load_schema())

   print(validator.is_valid({"value": {"kind": "currency", "currency": "USD"}}))

   error = best_match(validator.iter_errors({"value": {"kind": "currency", "currency": "usd"}}))
   print(error.json_path, error.message)

.. code-block:: text

   True
   $.value.currency 'usd' does not match '^[A-Z]{3}$'

Validators that do not support the OpenAPI ``discriminator`` keyword, which includes
``jsonschema``, try every kind in turn. For an unknown kind they report only that ``value``
matches none of them. :py:func:`validate_block` names the kind and lists the valid ones.

Copy the schema for other languages
-----------------------------------

To use the schema outside Python, copy the file into your project or build:

.. code-block:: python

   import shutil

   from s_layer_semantic_formats import SCHEMA_PATH

   shutil.copyfile(SCHEMA_PATH, "s_layer.schema.json")

Any draft 2020-12 validator can then load ``s_layer.schema.json``. Copy it again when you
upgrade the package, so the copy matches the version your Python code uses.

If the tool has no Python at all, take the file from the `source repository
<https://github.com/s-layer/semantic-formats/tree/main/src/s_layer_semantic_formats>`_
instead. Use the release tag (``v0.1.0`` and so on) that matches the package version the
Python side of your system uses.

Know what the schema does not check
-----------------------------------

The schema checks the shape of each key. Rules that depend on the member type or compare one
section with another are checked only by :py:func:`validate_block`:

- which kinds apply to a metric, fact or dimension, and ``aggregation`` only on metrics;
- ``display`` keys that fit the kind (and ``grouping`` only ``false`` on an
  ``identifier``), ``time`` only on ``date`` and ``datetime``, and no sub-day grain on a
  ``date``;
- ``aggregation`` on ``percentage`` and ``score`` being ``non_additive``;
- ``by`` being present exactly when ``additivity`` is ``semi_additive``;
- ``decimals`` ``min`` not above ``max``, and a score ``range`` with ``min`` below ``max``;
- whole numbers written as ``2.0``, and ``NaN`` or ``Infinity`` in extension values.

So a block can pass the schema and still be invalid:

.. code-block:: python

   from jsonschema import Draft202012Validator

   from s_layer_semantic_formats import SLayerValidationError, load_schema, validate_block

   data = {"value": {"kind": "currency", "currency": "USD"}, "display": {"date_style": "short"}}

   print(Draft202012Validator(load_schema()).is_valid(data))
   try:
       validate_block(data, "metric")
   except SLayerValidationError as error:
       print(error)

.. code-block:: text

   True
   invalid s_layer block (1 problem):
     display.date_style: not allowed on kind 'currency'

Use the schema for early feedback, and run :py:func:`validate_block` wherever a block is
accepted for real.

Troubleshooting
---------------

The schema accepts ``null`` for an optional key
   This is intended: ``null`` means the key is absent, as it does for
   :py:func:`validate_block`.

:py:func:`json_schema` and :py:func:`load_schema` both exist
   :py:func:`json_schema` generates the schema from the models at runtime and
   :py:func:`load_schema` reads the shipped file. In a released package they are equal; use
   :py:func:`load_schema`.

See also
--------

- :ref:`howto-validate-a-block` for the full check in Python.
- :ref:`explanation-design-decisions` lists every rule, including the ones the schema leaves
  out.
- :py:func:`load_schema` and :py:data:`SCHEMA_PATH` in the API reference.
