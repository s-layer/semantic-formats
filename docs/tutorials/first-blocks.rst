.. meta::
   :description: Write s_layer blocks in a dbt YAML file, check them with Python, fix an error and see the normal form

.. py:currentmodule:: s_layer_semantic_formats

.. _tutorial-first-blocks:

Check the s_layer blocks in a dbt file
======================================

In this tutorial you write ``s_layer`` blocks for two metrics and a date dimension in a dbt
YAML file, check them with a short Python script, fix the mistake it finds, and then look at
the two forms the library turns a block into. It takes about ten minutes.

You do not need a dbt project or a warehouse. A text editor, a terminal and Python 3.11 or
later are enough.

Install the package
-------------------

Create a new directory for this tutorial, open a terminal in it, and install the package
together with PyYAML, which the script uses to read the YAML file:

.. code-block:: bash

   pip install s-layer-semantic-formats pyyaml

Write the dbt YAML
------------------

Save this as ``metrics.yml``. It is a cut-down dbt property file: one semantic model with an
``order_date`` dimension, and two metrics. Each of these *members* carries an ``s_layer``
block under ``config.meta``.

.. code-block:: yaml
   :caption: metrics.yml

   semantic_models:
     - name: orders
       model: ref('orders')
       dimensions:
         - name: order_date
           type: time
           type_params:
             time_granularity: day
           config:
             meta:
               s_layer:
                 value: {kind: date}
                 time: {grain: day, fiscal_year_start: 4}

   metrics:
     - name: revenue
       type: simple
       type_params:
         measure: revenue
       config:
         meta:
           s_layer:
             value: {kind: currency, currency: usd}
             display: {decimals: {max: 0}, compact: auto}
             synonyms: [sales, turnover]

     - name: conversion_rate
       type: ratio
       type_params:
         numerator: orders
         denominator: sessions
       config:
         meta:
           s_layer:
             value: {kind: percentage}
             display: {decimals: [1, 1]}

The ``value`` section says what the numbers mean (money in a currency, a percentage, a
date). ``display`` and ``time`` add hints for showing them. The
:ref:`explanation-the-block` page describes every section.

Check the blocks
----------------

Save this script as ``check_blocks.py`` in the same directory. It reads the YAML, finds every
``s_layer`` block, and checks it with :py:func:`validate_block`, telling it whether the
block belongs to a metric or a dimension:

.. code-block:: python
   :caption: check_blocks.py

   import yaml

   from s_layer_semantic_formats import SLayerValidationError, validate_block

   with open("metrics.yml") as file:
       project = yaml.safe_load(file)

   members = [(metric, "metric") for metric in project["metrics"]]
   for model in project["semantic_models"]:
       members += [(dimension, "dimension") for dimension in model["dimensions"]]

   for member, member_type in members:
       data = member["config"]["meta"]["s_layer"]
       try:
           validate_block(data, member_type)
       except SLayerValidationError as error:
           print(f"{member['name']}: {error}")
       else:
           print(f"{member['name']}: ok")

Run it:

.. code-block:: bash

   python check_blocks.py

You should see one problem, on ``revenue``:

.. code-block:: text

   revenue: invalid s_layer block (1 problem):
     value.currency: String should match pattern '^[A-Z]{3}$'
   conversion_rate: ok
   order_date: ok

The path ``value.currency`` points at the key that is wrong, and the message says what it
must look like: three upper-case letters, an ISO 4217 currency code.

Fix the error
-------------

Change ``usd`` to ``USD`` in ``metrics.yml``. The whole file now reads:

.. code-block:: yaml
   :caption: metrics.yml
   :emphasize-lines: 23

   semantic_models:
     - name: orders
       model: ref('orders')
       dimensions:
         - name: order_date
           type: time
           type_params:
             time_granularity: day
           config:
             meta:
               s_layer:
                 value: {kind: date}
                 time: {grain: day, fiscal_year_start: 4}

   metrics:
     - name: revenue
       type: simple
       type_params:
         measure: revenue
       config:
         meta:
           s_layer:
             value: {kind: currency, currency: USD}
             display: {decimals: {max: 0}, compact: auto}
             synonyms: [sales, turnover]

     - name: conversion_rate
       type: ratio
       type_params:
         numerator: orders
         denominator: sessions
       config:
         meta:
           s_layer:
             value: {kind: percentage}
             display: {decimals: [1, 1]}

Run the script again:

.. code-block:: bash

   python check_blocks.py

Every block passes:

.. code-block:: text

   revenue: ok
   conversion_rate: ok
   order_date: ok

Look at the normal form
-----------------------

A valid block can be written in more than one way: ``decimals: {max: 0}`` and
``decimals: [0, 0]`` mean the same thing. The library turns every block into one *normal
form*, with the defaults filled in, so that tools can compare blocks and store them.

Save this second script as ``show_revenue.py``:

.. code-block:: python
   :caption: show_revenue.py

   import json

   import yaml

   from s_layer_semantic_formats import normalize, spec_tag_value, validate_block

   with open("metrics.yml") as file:
       project = yaml.safe_load(file)

   revenue = project["metrics"][0]["config"]["meta"]["s_layer"]
   block = validate_block(revenue, "metric")

   print(json.dumps(normalize(block), indent=2))
   print(spec_tag_value(block))

Run it:

.. code-block:: bash

   python show_revenue.py

You should see the normal form, then a single line of compact JSON:

.. code-block:: text

   {
     "display": {
       "compact": "auto",
       "decimals": [
         0,
         0
       ],
       "grouping": true,
       "negative": "minus"
     },
     "synonyms": [
       "sales",
       "turnover"
     ],
     "value": {
       "currency": "USD",
       "kind": "currency"
     }
   }
   {"display":{"compact":"auto","decimals":[0,0],"grouping":true,"negative":"minus"},"value":{"currency":"USD"}}

Compare the normal form with what you wrote in ``metrics.yml``:

- ``decimals: {max: 0}`` became the pair ``[0, 0]``, because ``min`` defaults to 0.
- ``negative: minus`` and ``grouping: true`` appeared. They are the defaults for every
  numeric kind, so the library writes them in.
- The keys are sorted.

The last line is the value that dbt-s-layer writes into a Snowflake or DuckDB tag called
``S_LAYER_SPEC``. It leaves out ``value.kind`` and the synonyms, because those travel
separately.

What you learned
----------------

- An ``s_layer`` block sits under ``config.meta`` on a dbt metric, fact or dimension.
- :py:func:`validate_block` checks a block for its member type and raises
  :py:class:`SLayerValidationError` listing each problem with its path.
- :py:func:`normalize` returns the normal form, with defaults filled in and keys sorted.
- :py:func:`spec_tag_value` returns the compact payload for the ``S_LAYER_SPEC`` tag.

Next steps
----------

- :ref:`howto-write-a-block` shows every kind and section you can use in your own YAML.
- :ref:`howto-validate-a-block` covers validation in your own tool, including how to report
  every problem.
- :ref:`explanation-normal-form` explains why the normal form exists and how equality
  works.
