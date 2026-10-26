.. meta::
   :description: Task-focused guides for writing, validating, comparing and transporting s_layer blocks

.. _how-to:

How-to guides
=============

Each guide solves one task. They assume you know what an ``s_layer`` block is; the
:ref:`tutorials` cover that.

For dbt YAML authors
--------------------

- :ref:`howto-write-a-block` -- Pick a kind for a metric, fact or dimension, fill its
  required keys and add display, time and aggregation hints.

For tool builders
-----------------

- :ref:`howto-validate-a-block` -- Validate blocks in your own tool and report every problem
  with its path.
- :ref:`howto-compare-blocks` -- Compare blocks by meaning, store their normal form and
  detect drift between YAML and a warehouse.
- :ref:`howto-round-trip-tags` -- Write a block as ``S_LAYER_KIND``, ``S_LAYER_SPEC`` and
  ``S_LAYER_LABEL`` tag values and rebuild it from them.
- :ref:`howto-use-the-json-schema` -- Check block shape with the packaged JSON Schema, in
  Python or another language.

.. toctree::
   :hidden:

   write-a-block
   validate-a-block
   compare-blocks
   round-trip-tags
   use-the-json-schema
