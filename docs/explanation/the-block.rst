.. meta::
   :description: What the s_layer block is, how its sections divide the work, and where a block travels

.. py:currentmodule:: s_layer_semantic_formats

.. _explanation-the-block:

Understanding the s_layer block
===============================

A dbt metric says how to compute a number. It does not say whether that number is money,
a ratio or a count of seconds, so every dashboard and query tool has to guess, or be told
again. The ``s_layer`` block is where that meaning is written down once, next to the metric,
fact or dimension it describes.

This page explains what goes in a block, why it is split into sections, and how a block
moves from dbt YAML to a warehouse and back.

What a block describes
----------------------

A block is a small mapping under ``config.meta.s_layer`` on one member of a semantic layer.
A *member* is a metric, a fact or a dimension, and which of the three it is, its *member
type*, matters: a percentage makes sense as a metric, but not as a dimension.

.. code-block:: yaml

   metrics:
     - name: revenue
       config:
         meta:
           s_layer:
             value: {kind: currency, currency: USD}
             display: {decimals: {max: 0}, compact: auto}
             synonyms: [sales, turnover]

The block says nothing about how ``revenue`` is computed. That stays in dbt. It only says
what the values are and how a reader should show them.

The sections
------------

Each section answers one question, so a tool can read only the part it cares about.

``value``: what the values mean
   The one required section. Its ``kind`` names the type of value, and the kind's own keys
   pin it down: ``currency`` needs the currency code, ``duration`` its unit, ``score`` its
   range. A chart library that only needs to know "this is money in USD" reads this section
   and nothing else.

``display``: how to show them
   Hints such as the number of decimals, compact notation (``1.2M``), how to show negative
   numbers, thousands separators and date style. They are suggestions for a renderer; the
   meaning stays in ``value``. Each hint applies only to kinds where it makes sense, so
   ``decimals`` fits a currency and ``date_style`` fits a date.

``time``: how a date axis behaves
   The grain and the month the fiscal year starts in. Only ``date`` and ``datetime``
   dimensions are a time axis, so only they take this section.

``aggregation``: how a metric adds up
   Whether a metric can be summed across every dimension, only some, or none. It belongs on
   metrics, and only when nothing upstream already says it: dbt metric types and
   non-additive dimension settings are the first place to declare this.

``label`` and ``synonyms``: names
   A display name and other names for search and natural-language tools. Many platforms have
   their own fields for these, so they belong in the block only where the platform has no
   such slot. The tool that writes the block decides that.

``x-`` keys: everything else
   Any key that starts with ``x-`` is an extension. The package keeps it as it is and gives
   it no meaning, so a team can carry its own data without forking the vocabulary.

Kinds and member types
----------------------

The fourteen kinds split along the member types. Metrics and facts are numbers you can
aggregate; dimensions are what you group and filter by.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Member types
     - Kinds
   * - metric only
     - ``count``, ``percentage``, ``bytes``, ``score``
   * - metric or fact
     - ``number``, ``currency``, ``duration``, ``quantity``
   * - dimension only
     - ``category``, ``geo``, ``date``, ``datetime``, ``identifier``, ``boolean``

Two of the metric kinds carry a rule of their own. Summing percentages or scores gives
nonsense (two conversion rates of 10% do not add up to 20%), so ``percentage`` and ``score``
are *non-additive* without being told, and :py:attr:`SLayerBlock.additivity` reports that.

:py:data:`KIND_MEMBER_TYPES` holds this table as data.

Where a block travels
---------------------

The package itself does no I/O and knows nothing about dbt or warehouses. It is the shared
definition that two other tools rely on:

1. An analytics engineer writes the block in dbt YAML.
2. **dbt-s-layer** validates it for the member type and writes it into each warehouse.
   Snowflake and DuckDB semantic views get tags: ``S_LAYER_KIND`` holds the kind,
   ``S_LAYER_SPEC`` the rest of the block as compact JSON, ``S_LAYER_LABEL`` the label,
   and synonyms go in the view's own synonyms clause.
3. **semolina** reads the tags back and rebuilds the block from them.

Both tools must agree on every detail: which keys exist, which defaults apply, and how the
compact JSON is written. If dbt-s-layer wrote ``decimals: {max: 0}`` and semolina expected
``[0, 0]``, the round trip would fail. Putting the models, the normal form and the tag
format in one package removes that risk. :ref:`explanation-normal-form` explains how the
package makes sure the block read back equals the block written.

See also
--------

- :ref:`howto-write-a-block` lists every key in each section.
- :ref:`explanation-normal-form` explains defaults and equality.
- :ref:`explanation-design-decisions` covers the rules that are not obvious from the keys.
