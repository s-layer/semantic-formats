.. meta::
   :description: Compare s_layer blocks by meaning, store their normal form and detect drift between YAML and a warehouse

.. py:currentmodule:: s_layer_semantic_formats

.. _howto-compare-blocks:

Compare blocks and detect drift
===============================

Two blocks written differently can mean the same thing. Use this guide when your tool needs
to tell whether two blocks are the same, store a block in a stable form, or check that what a
warehouse holds still matches the dbt YAML.

Before you start
----------------

- Install the package: ``pip install s-layer-semantic-formats``.
- The blocks you compare must be valid. See :ref:`howto-validate-a-block`.

Compare two blocks
------------------

Compare parsed blocks with ``==``. Equality is defined on the normal form, so blocks that
differ only in how they are written are equal:

.. code-block:: python

   from s_layer_semantic_formats import validate_block

   short = validate_block(
       {"value": {"kind": "currency", "currency": "USD"}, "display": {"decimals": {"max": 2}}},
       "metric",
   )
   spelled_out = validate_block(
       {
           "value": {"kind": "currency", "currency": "USD"},
           "display": {"decimals": [0, 2], "negative": "minus", "grouping": True},
       },
       "metric",
   )

   print(short == spelled_out)

.. code-block:: text

   True

A key the package does not fill in is different from leaving it out. ``compact: none``
states a choice; a missing ``compact`` leaves it to the reader:

.. code-block:: python

   from s_layer_semantic_formats import validate_block

   unset = validate_block({"value": {"kind": "count"}}, "metric")
   stated = validate_block({"value": {"kind": "count"}, "display": {"compact": "none"}}, "metric")

   print(unset == stated)

.. code-block:: text

   False

:ref:`explanation-normal-form` lists which defaults are filled in and why.

Use blocks as keys
------------------

Blocks are frozen and hash on the same normal form, so you can put them in a set or use them
as dictionary keys. This groups members that share a format:

.. code-block:: python

   from collections import defaultdict

   from s_layer_semantic_formats import validate_block

   metrics = {
       "revenue": {"value": {"kind": "currency", "currency": "USD"}},
       "refunds": {"value": {"kind": "currency", "currency": "USD"}, "display": {}},
       "conversion_rate": {"value": {"kind": "percentage"}},
   }

   by_format = defaultdict(list)
   for name, data in metrics.items():
       by_format[validate_block(data, "metric")].append(name)

   for names in by_format.values():
       print(names)

.. code-block:: text

   ['revenue', 'refunds']
   ['conversion_rate']

An empty ``display: {}`` says nothing, so ``refunds`` groups with ``revenue``.

Store the normal form
---------------------

To store a block, or to diff it in a review, save its normal form from
:py:func:`normalize`. It is plain JSON-ready data with sorted keys:

.. code-block:: python

   import json

   from s_layer_semantic_formats import normalize

   stored = json.dumps(normalize({"value": {"kind": "percentage"}}), sort_keys=True)
   print(stored)

.. code-block:: text

   {"display": {"grouping": true, "negative": "minus"}, "value": {"kind": "percentage", "scale": "fraction"}}

:py:func:`normalize` accepts a parsed block or a mapping, and raises
:py:class:`SLayerValidationError` if a mapping is not a valid block. Loading the stored JSON
with :py:func:`parse_block` gives back an equal block.

Detect drift between YAML and a warehouse
-----------------------------------------

To check that a warehouse member still matches the YAML, rebuild the block from the tags
read back from the warehouse with :py:func:`from_compact_json` and compare it with the block
from YAML:

.. code-block:: python

   from s_layer_semantic_formats import from_compact_json, validate_block

   in_yaml = validate_block(
       {
           "value": {"kind": "currency", "currency": "USD"},
           "display": {"decimals": {"max": 0}, "compact": "auto"},
       },
       "metric",
   )

   # Tag values as read back from the warehouse
   tags = {
       "S_LAYER_KIND": "currency",
       "S_LAYER_SPEC": '{"display":{"decimals":[0,0],"grouping":true,"negative":"minus"},'
       '"value":{"currency":"USD"}}',
   }
   in_warehouse = from_compact_json(tags["S_LAYER_KIND"], tags["S_LAYER_SPEC"])

   if in_warehouse != in_yaml:
       print("drift: warehouse", in_warehouse.normal_form()["display"])
       print("drift: yaml     ", in_yaml.normal_form()["display"])

.. code-block:: text

   drift: warehouse {'decimals': [0, 0], 'grouping': True, 'negative': 'minus'}
   drift: yaml      {'compact': 'auto', 'decimals': [0, 0], 'grouping': True, 'negative': 'minus'}

Here the warehouse is missing ``compact: auto``, so the member needs to be written again.
:ref:`howto-round-trip-tags` covers reading and writing the tags.

Troubleshooting
---------------

Two blocks look the same but are not equal
   Check optional keys that have no default, such as ``compact`` or ``date_style``: one block
   may state them and the other leave them out. Also check extension values: equality
   compares JSON text, so ``1``, ``1.0`` and ``true`` are three different values.

Comparing a block with a plain dictionary returns ``False``
   ``==`` compares blocks with blocks. Parse the dictionary first with :py:func:`parse_block`,
   or compare :py:func:`normalize` results.

See also
--------

- :ref:`explanation-normal-form` explains how the normal form is built.
- :ref:`howto-round-trip-tags` shows how tags are written and read.
- :py:meth:`SLayerBlock.normal_form` in the API reference.
