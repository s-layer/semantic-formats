.. meta::
   :description: The S-LAYER semantic format vocabulary: typed models, normal form and JSON Schema

========================
s-layer-semantic-formats
========================

The S-LAYER semantic format vocabulary: typed models, normal form and JSON Schema

Installation
------------

.. code-block:: bash

   pip install s-layer-semantic-formats

Or with `uv <https://docs.astral.sh/uv/>`_:

.. code-block:: bash

   uv add s-layer-semantic-formats

Quick Start
-----------

Validate a block for a member type, then compare or serialise its normal form:

.. code-block:: python

   from s_layer_semantic_formats import normalize, spec_tag_value, validate_block

   block = validate_block(
       {"value": {"kind": "currency", "currency": "USD"}, "display": {"decimals": {"max": 0}}},
       "metric",
   )
   normalize(block)  # JSON-ready data with the defaults filled in
   spec_tag_value(block)  # the S_LAYER_SPEC tag payload, at most 256 characters

The README lists the whole public API and the rules the package applies where the design
doc is silent.

.. toctree::
   :hidden:

   API Reference <autoapi/index>
   Release notes <changelog>
