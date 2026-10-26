.. meta::
   :description: Why blocks have a normal form, which defaults it fills in, how equality works and how S_LAYER_SPEC derives from it

.. py:currentmodule:: s_layer_semantic_formats

.. _explanation-normal-form:

The normal form and equality
============================

YAML lets the same block be written many ways. Decimals can be ``{max: 2}``, ``{min: 0,
max: 2}`` or ``[0, 2]``; a default can be written out or left implicit; keys come in any
order. Tools that write a block and tools that read it back must still agree on whether two
blocks are the same. The package settles this with a single *normal form* for every valid
block, and defines equality on it.

What the normal form is
-----------------------

The normal form is the block as plain JSON-ready data, built by a fixed set of steps:

- the defaults the vocabulary defines are filled in;
- optional keys that are absent (or ``null``) are left out, and so is an empty section such
  as ``display: {}``;
- ``decimals`` becomes a ``[min, max]`` pair;
- whole-number score bounds become integers, so ``[0.0, 10]`` and ``[0, 10]`` agree;
- object keys are sorted. List order is kept, because it can carry meaning: a category's
  ``order`` is its ranking.

:py:func:`normalize` returns it, as does :py:meth:`SLayerBlock.normal_form`:

.. code-block:: pycon

   >>> from s_layer_semantic_formats import normalize
   >>> block = {"value": {"kind": "score", "range": [0.0, 10]}, "display": {"decimals": {"max": 1}}}
   >>> normalize(block)
   {'display': {'decimals': [0, 1], 'grouping': True, 'negative': 'minus'}, 'value': {'kind': 'score', 'range': [0, 10]}}

Which defaults are filled in
----------------------------

Only the defaults the design doc states are filled in:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Where
     - Default
   * - ``percentage``
     - ``scale: fraction``
   * - ``bytes``
     - ``unit: B``
   * - ``decimals``
     - ``min: 0``
   * - every numeric kind
     - ``negative: minus`` and ``grouping: true``
   * - ``identifier``
     - ``grouping: false``

Every other optional key, such as ``compact``, ``date_style``, ``grain``,
``fiscal_year_start``, a geo ``code`` or a number's ``unit``, stays out of the normal form
when it is not written. This is a deliberate choice: a missing ``compact`` means "the reader
decides", while ``compact: none`` means "never abbreviate". Filling in a guess would erase
that difference, so the two blocks are not equal.

.. code-block:: pycon

   >>> from s_layer_semantic_formats import parse_block
   >>> parse_block({"value": {"kind": "count"}}) == parse_block(
   ...     {"value": {"kind": "count"}, "display": {"compact": "none"}}
   ... )
   False

Implied values that are not filled in
-------------------------------------

``percentage`` and ``score`` are always non-additive. That rule is exposed by
:py:func:`implied_additivity` and :py:attr:`SLayerBlock.additivity`, but it is not written
into the normal form. The normal form holds an ``aggregation`` section only when someone
wrote one.

.. code-block:: pycon

   >>> from s_layer_semantic_formats import parse_block
   >>> block = parse_block({"value": {"kind": "percentage"}})
   >>> block.additivity
   'non_additive'
   >>> "aggregation" in block.normal_form()
   False

The reason is "derive, don't duplicate". A reader can work the additivity out from the kind,
so copying it into every block would only add a second place for it to go wrong.

How equality works
------------------

Two :py:class:`SLayerBlock` objects are equal when the canonical JSON text of their normal
forms is equal: sorted keys, no whitespace and non-ASCII characters written as they are.
Hashing uses the same text, so equal blocks hash alike and work as set members and dictionary keys.

Comparing text rather than Python values has one visible effect. In Python, ``1 == 1.0 ==
True``. In JSON text they are ``1``, ``1.0`` and ``true``. Inside extension values, which the
package keeps exactly as written, those are three different blocks:

.. code-block:: pycon

   >>> from s_layer_semantic_formats import parse_block
   >>> parse_block({"value": {"kind": "count"}, "x-rank": 1}) == parse_block(
   ...     {"value": {"kind": "count"}, "x-rank": 1.0}
   ... )
   False

Comparing text gives an answer that a tool in any language can reproduce from the same JSON,
without depending on how that language compares numbers and booleans.

How S_LAYER_SPEC derives from the normal form
---------------------------------------------

A Snowflake tag value holds at most 256 characters, so the block is split across several
tags. The ``S_LAYER_SPEC`` payload is the canonical JSON text of the normal form with three
things taken out:

- ``value.kind``, which goes in its own ``S_LAYER_KIND`` tag;
- ``label``, which goes in ``S_LAYER_LABEL``;
- ``synonyms``, which go in the platform's native synonyms clause.

The rest keeps the block's nesting. If ``value`` is left empty it is dropped, so a plain
``date`` dimension has the payload ``{}``:

.. code-block:: pycon

   >>> from s_layer_semantic_formats import to_compact_json
   >>> to_compact_json({"value": {"kind": "date"}})
   '{}'
   >>> to_compact_json({"value": {"kind": "duration", "unit": "s"}, "label": "Session length"})
   '{"display":{"grouping":true,"negative":"minus"},"value":{"unit":"s"}}'

Because the payload is derived from the normal form, it is the same string for every way of
writing the same block. Reading it back with :py:func:`from_compact_json` gives a block equal
to the original, which is what lets dbt-s-layer and semolina agree without talking to each
other. Non-ASCII text is written as is, and the 256-character limit counts characters, not
bytes. :py:func:`spec_tag_value` refuses a longer payload rather than truncating it, because
a truncated payload would not be JSON.

See also
--------

- :ref:`howto-compare-blocks` puts equality to work.
- :ref:`howto-round-trip-tags` writes and reads the tags.
- :ref:`explanation-design-decisions` lists every rule behind the normal form.
