.. meta::
   :description: The rules the package applies where the S-LAYER design doc is silent, grouped by theme, with the reasoning

.. py:currentmodule:: s_layer_semantic_formats

.. _explanation-design-decisions:

Design decisions
================

The S-LAYER vocabulary comes from a design doc that is still a draft. It names the kinds, the
sections and most of the keys, but it leaves many details open: which keys are required,
which values are allowed, how strict to be. Where the doc is silent, this package picks the
simplest rule it could find, and applies it the same way everywhere: in
:py:func:`validate_block`, in the normal form and, where JSON Schema can express it, in the
schema.

This page groups those rules by theme. The numbers in brackets match the "Decisions not in
the design doc" list in the project README.

Defaults: only the stated ones
------------------------------

The normal form fills in only the defaults the doc states: percentage ``scale: fraction``,
bytes ``unit: B``, decimals ``min: 0``, and ``negative: minus`` and ``grouping: true`` on
numeric kinds, with ``grouping: false`` on ``identifier`` [1]. Every other optional key is
left out when absent, so a missing ``compact`` is not the same as ``compact: none``.

Implied additivity follows the same restraint. ``percentage`` and ``score`` imply
``non_additive``, and :py:func:`implied_additivity` and :py:attr:`SemanticFormat.additivity`
report it, but the normal form and ``S_LAYER_SPEC`` carry an ``aggregation`` only when
someone wrote one: derive, don't duplicate. A stated ``aggregation`` on those two kinds must
be ``non_additive`` [2].

:ref:`explanation-normal-form` explains why an absent key and an explicit one must stay
different.

What each kind requires and allows
----------------------------------

Required keys
   ``duration.unit``, ``score.range`` and ``geo.level`` are required, because their rows in
   the doc have neither a ``?`` nor a default. ``boolean.labels``, when given, needs both
   ``true`` and ``false``. dbt reads unquoted ``true:`` and ``false:`` keys as booleans, so
   those are accepted as well [3].

Open value lists
   Bytes units are ``B``, ``KB`` to ``EB`` and ``KiB`` to ``EiB``. A number's optional
   ``unit`` is any non-empty string, like a quantity's UCUM code. A currency is checked only
   against the pattern ``^[A-Z]{3}$``, not against a list of ISO 4217 codes, and a geo
   ``code`` is any non-empty string [4]. The currency pattern catches mistakes such as
   ``usd``, but it does not check that a code is actually assigned.

Score ranges
   A range is two finite numbers with ``min < max``. Whole numbers are written as integers in
   the normal form, so ``[0.0, 10]`` and ``[0, 10]`` are equal [5].

Decimals
   Whole numbers from 0 to 20, with ``max`` required whenever ``decimals`` is given and
   ``min <= max``. Both ``{min, max}`` and ``[min, max]`` are accepted, and the normal form
   is the pair [6].

Keys must fit the kind
----------------------

Some keys only make sense for some kinds, and the package rejects them elsewhere rather
than ignoring them:

- ``decimals``, ``compact`` and ``negative`` only on numeric kinds; ``grouping`` on numeric
  kinds and on ``identifier``, where only ``false`` is allowed; ``date_style`` only on
  ``date`` and ``datetime`` [7].
- ``time`` only on ``date`` and ``datetime``, and a ``date`` cannot take a grain finer than a
  day (``second``, ``minute``, ``hour``) [8].
- ``aggregation`` only on metrics, a check :py:func:`validate_block` makes because it is the
  call that knows the member type. ``by`` is required exactly when ``additivity`` is
  ``semi_additive`` [9].

Rejecting a misplaced key catches mistakes early. A ``date_style`` on a currency metric is
almost certainly on the wrong member, and silently ignoring it would hide that.

Lists, labels and extensions
----------------------------

Lists
   ``category.order``, ``aggregation.by`` and ``synonyms`` are non-empty lists of distinct,
   non-empty strings. Their order is kept, since it can carry meaning [10].

Labels
   A ``label`` is 1 to 255 characters, which fits both the Databricks ``display_name`` limit
   of 255 and the 256-character tag limit. Whether a platform has a native label or synonyms
   slot, and so whether ``label`` or ``synonyms`` belong in the block at all, is left to
   dbt-s-layer [11].

Extension keys
   Extension keys are allowed on the block and on ``value``, ``display``, ``time`` and
   ``aggregation``, but not inside ``decimals``, ``labels`` or ``range``. A key is an
   extension when it starts with lower-case ``x-`` and has at least one more character.
   Values can be any JSON, so ``NaN`` and ``Infinity`` are not allowed, and they are kept as
   written; only the key order of objects is sorted in the normal form [12].

Absence and strictness
----------------------

``null`` means absent
   ``null`` for any optional key is the same as leaving the key out, and an empty
   ``display: {}`` or ``time: {}`` is the same as no section [13]. YAML makes it easy to
   leave a key with no value, and treating that as "not set" is what an author means.

No type coercion
   Scalars are strict: a string is never read as a number or a boolean, and a boolean is
   never read as a number. ``grouping: "yes"``, ``fiscal_year_start: "4"`` and
   ``decimals.max: 2.0`` are all errors [14]. Every reader of a block, in any language, then
   sees the same value the author wrote.

The tag payload and equality
----------------------------

The payload keeps the block's shape
   ``S_LAYER_SPEC`` keeps the block's nesting, ``{"display": {...}, "value": {...}}``, minus
   ``value.kind``, ``label`` and ``synonyms``. An empty ``value`` object is dropped, so a bare
   ``date`` block's payload is ``{}``. Non-ASCII text is written as is, and the 256 limit
   counts characters and is inclusive. :py:func:`from_compact_json` rejects a payload that
   contains ``kind``, ``label`` or ``synonyms``, or ``NaN`` or ``Infinity``. It treats an
   empty label or synonyms list as none, and rejects a bare string of synonyms [15].

Equality is on text
   Two blocks are equal when the canonical JSON text of their normal forms is equal, so
   extension values ``1``, ``1.0`` and ``true`` are different [16].
   :ref:`explanation-normal-form` explains why text, not Python values.

What the JSON Schema covers
---------------------------

The schema checks shape only [17]. These rules are enforced by the Python models and
:py:func:`validate_block`, not by the schema:

- which kinds apply to which member type, and the rules between sections from [2], [7], [8]
  and [9];
- a few rules within one key: ``2.0`` where an integer is required [14], ``min <= max`` for
  decimals and ``min < max`` for a score range [5, 6], ``by`` being present exactly when
  ``semi_additive`` [9], and finite extension values [12].

So a block that passes the schema can still fail :py:func:`validate_block`. The schema
accepts ``null`` for optional keys, matching [13]. JSON Schema can express these rules only
awkwardly or not at all, and keeping them in one place means there is one implementation to
trust. :ref:`howto-use-the-json-schema` shows the difference in practice.

See also
--------

- :ref:`explanation-the-block` for what each section is for.
- :ref:`explanation-normal-form` for defaults and equality.
- :ref:`howto-write-a-block` for the keys as a checklist.
