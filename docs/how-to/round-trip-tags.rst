.. meta::
   :description: Write a block as S_LAYER_KIND, S_LAYER_SPEC and S_LAYER_LABEL tag values and rebuild it from them

.. py:currentmodule:: s_layer_semantic_formats

.. _howto-round-trip-tags:

Round-trip a block through warehouse tags
=========================================

Snowflake and DuckDB semantic views carry an ``s_layer`` block as tags on each member. Use
this guide when your tool writes those tags, as dbt-s-layer does, or reads them back, as
semolina does. Both directions use the same functions, so the block you read back is equal
to the one you wrote.

Before you start
----------------

- Install the package: ``pip install s-layer-semantic-formats``.
- Know which tags carry which part of the block:

  .. list-table::
     :header-rows: 1
     :widths: 25 75

     * - Where
       - What it holds
     * - ``S_LAYER_KIND`` tag
       - ``value.kind``, such as ``currency``
     * - ``S_LAYER_SPEC`` tag
       - The rest of the block as compact JSON, at most 256 characters
     * - ``S_LAYER_LABEL`` tag
       - ``label``, when the block has one
     * - The platform's own synonyms clause
       - ``synonyms``, when the block has them

  :ref:`explanation-normal-form` explains why the block is split this way.

Write the tags
--------------

Validate the block, then take each tag value from it. :py:func:`spec_tag_value` returns the
``S_LAYER_SPEC`` payload:

.. code-block:: python

   from s_layer_semantic_formats import spec_tag_value, validate_block

   block = validate_block(
       {
           "value": {"kind": "currency", "currency": "USD"},
           "display": {"decimals": {"max": 0}, "compact": "auto"},
           "label": "Revenue",
           "synonyms": ["sales", "turnover"],
       },
       "metric",
   )

   tags = {"S_LAYER_KIND": block.kind, "S_LAYER_SPEC": spec_tag_value(block)}
   if block.label is not None:
       tags["S_LAYER_LABEL"] = block.label
   synonyms = block.synonyms or []

   for name, value in tags.items():
       print(f"{name} = {value}")
   print("synonyms:", synonyms)

.. code-block:: text

   S_LAYER_KIND = currency
   S_LAYER_SPEC = {"display":{"compact":"auto","decimals":[0,0],"grouping":true,"negative":"minus"},"value":{"currency":"USD"}}
   S_LAYER_LABEL = Revenue
   synonyms: ['sales', 'turnover']

The payload has sorted keys and no whitespace, so the same block always produces the same
string. A block with nothing beyond its kind, such as a plain ``date`` dimension, has the
payload ``{}``.

Handle a payload that is too long
---------------------------------

A Snowflake tag value holds at most 256 characters (:py:data:`MAX_TAG_LENGTH`).
:py:func:`spec_tag_value` raises :py:class:`SpecTooLongError` instead of writing a longer
payload; it never truncates:

.. code-block:: python

   from s_layer_semantic_formats import SpecTooLongError, spec_tag_value, validate_block

   segments = [f"segment_{number:02d}" for number in range(20)]
   block = validate_block({"value": {"kind": "category", "order": segments}}, "dimension")

   try:
       spec_tag_value(block)
   except SpecTooLongError as error:
       print(f"{len(error.spec)} characters, limit {error.limit}")

.. code-block:: text

   281 characters, limit 256

The usual fix is in the YAML: shorten the longest values, here the category ``order``. If you
write to a platform with a different limit, pass it as ``limit``. To get the payload without
any length check, call :py:func:`to_compact_json`:

.. code-block:: python

   from s_layer_semantic_formats import spec_tag_value, to_compact_json

   # Using block from above
   print(len(spec_tag_value(block, limit=1000)), len(to_compact_json(block)))

.. code-block:: text

   281 281

Read the tags back
------------------

Pass the tag values to :py:func:`from_compact_json`. Give the label and synonyms as keyword
arguments; pass ``member_type`` to also check that the kind fits the member:

.. code-block:: python

   from s_layer_semantic_formats import from_compact_json, validate_block

   read = from_compact_json(
       "currency",
       '{"display":{"compact":"auto","decimals":[0,0],"grouping":true,"negative":"minus"},'
       '"value":{"currency":"USD"}}',
       label="Revenue",
       synonyms=["sales", "turnover"],
       member_type="metric",
   )

   written = validate_block(
       {
           "value": {"kind": "currency", "currency": "USD"},
           "display": {"decimals": {"max": 0}, "compact": "auto"},
           "label": "Revenue",
           "synonyms": ["sales", "turnover"],
       },
       "metric",
   )

   print(read == written)
   print(read.label, read.synonyms)

.. code-block:: text

   True
   Revenue ['sales', 'turnover']

A tag that is not set can be passed as ``None`` or ``""``, and an empty synonyms list is the
same as none:

.. code-block:: python

   from s_layer_semantic_formats import from_compact_json

   block = from_compact_json("date", None, label="", synonyms=[])
   print(block.normal_form())

.. code-block:: text

   {'value': {'kind': 'date'}}

Troubleshooting
---------------

:py:func:`from_compact_json` raises :py:class:`SLayerValidationError` when the tags do not
make a valid block. These messages point at the tag values rather than the YAML:

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Message
     - Cause
   * - ``(block): S_LAYER_SPEC is not JSON: ...``
     - The tag holds something other than JSON, or JSON with ``NaN`` or ``Infinity``.
   * - ``(block): S_LAYER_SPEC must be a JSON object``
     - The payload is a list, string or number.
   * - ``value.kind: must not appear in S_LAYER_SPEC; it is S_LAYER_KIND``
     - The payload repeats the kind. Pass it as the first argument only.
   * - ``label: must not appear in S_LAYER_SPEC``
     - The payload holds ``label`` or ``synonyms``. Pass them as keyword arguments.
   * - ``synonyms: must be a list of strings, not a string``
     - A single string was passed as ``synonyms``. Wrap it in a list.

.. code-block:: python

   from s_layer_semantic_formats import SLayerValidationError, from_compact_json

   try:
       from_compact_json("currency", '{"value":{"kind":"currency","currency":"USD"}}')
   except SLayerValidationError as error:
       print(error)

.. code-block:: text

   invalid s_layer block (1 problem):
     value.kind: must not appear in S_LAYER_SPEC; it is S_LAYER_KIND

See also
--------

- :ref:`howto-compare-blocks` uses the round trip to detect drift.
- :ref:`explanation-normal-form` explains how the payload is derived from the normal form.
- :py:func:`from_compact_json` and :py:func:`spec_tag_value` in the API reference.
