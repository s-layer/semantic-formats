.. meta::
   :description: Validate s_layer blocks in your own tool and report every problem with its path

.. py:currentmodule:: s_layer_semantic_formats

.. _howto-validate-a-block:

Validate a block and report its problems
========================================

Use this guide when your tool reads ``s_layer`` blocks, from dbt YAML, a dbt manifest or
anywhere else, and must reject invalid ones with a useful message before it does anything
with them.

Before you start
----------------

- Install the package: ``pip install s-layer-semantic-formats``.
- Have each block as a mapping, the value of ``config.meta.s_layer``, and know the member
  type it is attached to: ``"metric"``, ``"fact"`` or ``"dimension"``.

Validate for a member type
--------------------------

Call :py:func:`validate_block` with the block and its member type. It returns a typed
:py:class:`SLayerBlock` with the defaults filled in:

.. code-block:: python

   from s_layer_semantic_formats import validate_block

   block = validate_block(
       {
           "value": {"kind": "currency", "currency": "USD"},
           "display": {"decimals": {"max": 0}, "compact": "auto"},
       },
       "metric",
   )

   print(block.kind)
   print(block.value.currency)
   print(block.display.decimals.as_pair(), block.display.negative, block.display.grouping)

.. code-block:: text

   currency
   USD
   (0, 0) minus True

The block is frozen, so your tool can pass it around and use it as a dictionary key. The
defaults it fills in are listed in :ref:`explanation-normal-form`.

Report every problem
--------------------

When a block is invalid, :py:func:`validate_block` raises :py:class:`SLayerValidationError`.
Its message lists every problem, and its ``issues`` attribute holds each one as an
:py:class:`Issue` with a ``path`` and a ``message``:

.. code-block:: python

   from s_layer_semantic_formats import SLayerValidationError, validate_block

   data = {
       "value": {"kind": "currency", "currency": "usd"},
       "display": {"decimals": {"max": 2.0}},
       "colour": "red",
   }

   try:
       validate_block(data, "metric")
   except SLayerValidationError as error:
       print(error)
       for issue in error.issues:
           print(f"{issue.path!r} -> {issue.message}")

.. code-block:: text

   invalid s_layer block (3 problems):
     colour: unknown key; only 'x-' extension keys may be added
     value.currency: String should match pattern '^[A-Z]{3}$'
     display.decimals.max: Input should be a valid integer
   'colour' -> unknown key; only 'x-' extension keys may be added
   'value.currency' -> String should match pattern '^[A-Z]{3}$'
   'display.decimals.max' -> Input should be a valid integer

Paths are dotted, with list positions in brackets (``synonyms[1]``). A problem with the
block as a whole has an empty path, and prints as ``(block)``.

To collect problems across many members instead of stopping at the first bad one, catch the
error per member and keep its issues:

.. code-block:: python

   from s_layer_semantic_formats import SLayerValidationError, validate_block

   members = [
       ("revenue", "metric", {"value": {"kind": "currency", "currency": "USD"}}),
       ("order_count", "metric", {"value": {"kind": "count"}}),
       ("customer_region", "dimension", {"value": {"kind": "geo"}}),
       ("order_total", "fact", {"value": {"kind": "percentage"}}),
   ]

   problems = []
   for name, member_type, data in members:
       try:
           validate_block(data, member_type)
       except SLayerValidationError as error:
           problems += [(name, issue) for issue in error.issues]

   for name, issue in problems:
       print(f"{name}: {issue}")

.. code-block:: text

   customer_region: value.level: required key is missing
   order_total: value.kind: kind 'percentage' applies to a metric, not a fact

Parse now, check the member type later
--------------------------------------

If your tool reads blocks before it knows where they are attached, split the check in two.
:py:func:`parse_block` checks the block on its own, and :py:func:`member_type_issues`
returns the member-type problems as a list instead of raising:

.. code-block:: python

   from s_layer_semantic_formats import member_type_issues, parse_block

   block = parse_block({"value": {"kind": "number"}, "aggregation": {"additivity": "additive"}})

   print(member_type_issues(block, "metric"))
   for issue in member_type_issues(block, "dimension"):
       print(issue)

.. code-block:: text

   []
   value.kind: kind 'number' applies to a fact or metric, not a dimension
   aggregation: only allowed on a metric, not a dimension

:py:data:`KIND_MEMBER_TYPES` holds the same table as data, if you need it to build a
picker or your own message:

.. code-block:: python

   from s_layer_semantic_formats import KIND_MEMBER_TYPES

   print(sorted(KIND_MEMBER_TYPES["duration"]))

.. code-block:: text

   ['fact', 'metric']

Check the result
----------------

:py:func:`validate_block` also accepts a block it has already parsed, and returns it as it
is. Running it again is a cheap way to assert, at a boundary in your code, that a block is
valid for a member type:

.. code-block:: python

   from s_layer_semantic_formats import parse_block, validate_block

   block = parse_block({"value": {"kind": "count"}})
   print(validate_block(block, "metric") is block)

.. code-block:: text

   True

Troubleshooting
---------------

``ValueError: member_type must be one of metric, fact, dimension``
   The second argument is not one of the three member types. dbt measures and entities are
   not member types; pass the type of the metric, fact or dimension the block belongs to.

A block that passed before fails after a fix
   Rules that compare sections, such as a ``display`` key that does not fit the kind, are
   checked once every key has the right shape. Fixing shape problems can therefore reveal
   new ones.

A string such as ``"2"`` or ``"true"`` is rejected
   Values are not converted between types. If your loader produces strings, convert them
   before validating, or fix the source YAML.

Catching every error from the package
   :py:class:`SLayerValidationError` and :py:class:`SpecTooLongError` both derive from
   :py:class:`SLayerError` and from :py:class:`ValueError`.

See also
--------

- :ref:`howto-write-a-block` lists every key and the messages an analytics engineer will
  see.
- :ref:`howto-compare-blocks` shows what to do with valid blocks.
- :py:func:`validate_block` and :py:class:`SLayerValidationError` in the API reference.
