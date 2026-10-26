.. meta::
   :description: The S-LAYER semantic format vocabulary: typed models, normal form and JSON Schema

.. py:currentmodule:: s_layer_semantic_formats

========================
s-layer-semantic-formats
========================

A dbt metric says how to compute a number, not what the number is. The ``s_layer`` block,
written in dbt ``config.meta``, says what a metric, fact or dimension *means*: a currency in
USD, a fraction shown as a percentage, a duration in seconds, a date at month grain.

This package is the shared definition of that block. It gives you:

- typed pydantic v2 models for the block, and :py:func:`validate_block` to check one for a
  member type;
- the normal form that defines when two blocks are equal (:py:func:`normalize`);
- the compact ``S_LAYER_SPEC`` tag payload used by Snowflake and DuckDB semantic views, and
  its inverse;
- a JSON Schema generated from the models, shipped inside the package.

It contains no warehouse code and no dbt code. `dbt-s-layer
<https://github.com/s-layer/dbt-s-layer>`_ uses it to validate blocks and write them into each
warehouse; `semolina <https://github.com/s-layer/semolina>`_ uses it to read them back.

Installation
------------

The package needs Python 3.11 or later.

.. tab-set::
   :sync-group: installer

   .. tab-item:: pip
      :sync: pip

      .. code-block:: bash

         pip install s-layer-semantic-formats

   .. tab-item:: uv
      :sync: uv

      .. code-block:: bash

         uv add s-layer-semantic-formats

A first look
------------

An analytics engineer writes the block in YAML; a tool reads it with Python:

.. tab-set::
   :sync-group: view

   .. tab-item:: dbt YAML
      :sync: yaml

      .. code-block:: yaml

         metrics:
           - name: revenue
             config:
               meta:
                 s_layer:
                   value: {kind: currency, currency: USD}
                   display: {decimals: {max: 0}, compact: auto}

   .. tab-item:: Python
      :sync: python

      .. code-block:: python

         from s_layer_semantic_formats import normalize, spec_tag_value, validate_block

         block = validate_block(
             {
                 "value": {"kind": "currency", "currency": "USD"},
                 "display": {"decimals": {"max": 0}, "compact": "auto"},
             },
             "metric",
         )

         print(normalize(block))
         print(spec_tag_value(block))

      .. code-block:: text

         {'display': {'compact': 'auto', 'decimals': [0, 0], 'grouping': True, 'negative': 'minus'}, 'value': {'currency': 'USD', 'kind': 'currency'}}
         {"display":{"compact":"auto","decimals":[0,0],"grouping":true,"negative":"minus"},"value":{"currency":"USD"}}

Where to go next
----------------

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item-card:: Tutorial
      :link: tutorials
      :link-type: ref

      Write blocks in a dbt file, check them and fix an error, in about ten minutes.

   .. grid-item-card:: How-to guides
      :link: how-to
      :link-type: ref

      Write a block in YAML, validate blocks in your tool, compare them, round-trip tags
      and use the JSON Schema.

   .. grid-item-card:: Explanation
      :link: explanation
      :link-type: ref

      What the block's sections are for, how the normal form and equality work, and the
      rules behind them.

   .. grid-item-card:: Reference
      :link: reference
      :link-type: ref

      Every public function, model, error and constant, generated from the docstrings.

.. toctree::
   :hidden:

   tutorials/index
   how-to/index
   explanation/index
   reference/index
   Release notes <changelog>
