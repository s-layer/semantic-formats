.. meta::
   :description: Choose a kind, fill its required keys and add display, time and aggregation hints to a dbt member

.. py:currentmodule:: s_layer_semantic_formats

.. _howto-write-a-block:

Write an s_layer block in dbt YAML
==================================

This guide takes you from a dbt metric, fact or dimension to a valid ``s_layer`` block: pick
the kind, add the keys that kind needs, then add only the optional hints you want. Each step
lists the exact keys and values the package accepts.

Before you start
----------------

- Know whether the member is a **metric**, a **fact** or a **dimension**. This is its
  *member type*, and it decides which kinds you can use.
- To check the result (the last step), install the package and PyYAML:

  .. code-block:: bash

     pip install s-layer-semantic-formats pyyaml

The block always goes under ``config.meta.s_layer`` on the member:

.. code-block:: yaml

   metrics:
     - name: revenue
       type: simple
       type_params:
         measure: revenue
       config:
         meta:
           s_layer:
             value: {kind: currency, currency: USD}

Step 1: Pick a kind
-------------------

Every block needs a ``value`` section with a ``kind``. Pick the row that describes the
member's values, check that its member type is allowed, and add the required keys.

.. list-table::
   :header-rows: 1
   :widths: 14 18 30 38

   * - ``kind``
     - Member types
     - Required keys
     - Optional keys
   * - ``number``
     - metric, fact
     -
     - ``unit``: a UCUM unit code such as ``kg``
   * - ``count``
     - metric
     -
     -
   * - ``currency``
     - metric, fact
     - ``currency``: an ISO 4217 code such as ``USD``
     -
   * - ``percentage``
     - metric
     -
     - ``scale``: ``fraction`` (0.12 means 12%, the default) or ``percent`` (12 means 12%)
   * - ``duration``
     - metric, fact
     - ``unit``: ``ms``, ``s``, ``min``, ``h`` or ``d``
     -
   * - ``bytes``
     - metric
     -
     - ``unit``: ``B`` (the default), ``KB`` to ``EB``, or ``KiB`` to ``EiB``
   * - ``quantity``
     - metric, fact
     - ``unit``: a UCUM unit code such as ``km``
     -
   * - ``score``
     - metric
     - ``range``: ``[min, max]``, with min less than max
     -
   * - ``category``
     - dimension
     -
     - ``order``: the values in order, which makes the category ordinal
   * - ``geo``
     - dimension
     - ``level``: ``country``, ``region``, ``state``, ``city``, ``postal_code``,
       ``latitude`` or ``longitude``
     - ``code``: the coding scheme, such as ``iso3166-1-alpha-2``
   * - ``date``
     - dimension
     -
     -
   * - ``datetime``
     - dimension
     -
     -
   * - ``identifier``
     - dimension
     -
     -
   * - ``boolean``
     - dimension
     -
     - ``labels``: ``{true: ..., false: ...}``, both required when given

For example, a session-length metric measured in seconds and a ranked dimension:

.. code-block:: yaml

   metrics:
     - name: avg_session_duration
       config:
         meta:
           s_layer:
             value: {kind: duration, unit: s}

   semantic_models:
     - name: tickets
       dimensions:
         - name: priority
           type: categorical
           config:
             meta:
               s_layer:
                 value: {kind: category, order: [low, medium, high]}

.. tip::

   ``boolean`` labels can be written with unquoted ``true:`` and ``false:`` keys. dbt's
   YAML loader reads them as booleans, and the package accepts that.

Step 2: Add display hints (optional)
------------------------------------

``display`` says how to show the values. Every key is optional, and each one fits only some
kinds:

.. list-table::
   :header-rows: 1
   :widths: 16 44 24 16

   * - Key
     - Values
     - Kinds
     - Default
   * - ``decimals``
     - ``{min: 0, max: 2}`` or ``[0, 2]``; whole numbers 0 to 20, ``max`` required,
       ``min`` not above ``max``. ``min == max`` means exactly that many.
     - numeric kinds
     - ``min: 0``
   * - ``compact``
     - ``none``, ``auto``, ``thousands``, ``millions``, ``billions``
     - numeric kinds
     - not filled in
   * - ``negative``
     - ``minus`` or ``parentheses``
     - numeric kinds
     - ``minus``
   * - ``grouping``
     - ``true`` or ``false`` (thousands separators)
     - numeric kinds; ``identifier`` (``false`` only)
     - ``true``; ``false`` on ``identifier``
   * - ``date_style``
     - ``short``, ``medium``, ``long``, ``iso``
     - ``date``, ``datetime``
     - not filled in

The numeric kinds are ``number``, ``count``, ``currency``, ``percentage``, ``duration``,
``bytes``, ``quantity`` and ``score``.

.. code-block:: yaml

   metrics:
     - name: revenue
       config:
         meta:
           s_layer:
             value: {kind: currency, currency: USD}
             display:
               decimals: {max: 0}
               compact: auto
               negative: parentheses

Step 3: Add time settings (date and datetime dimensions only)
-------------------------------------------------------------

``time`` is allowed only on ``date`` and ``datetime`` dimensions:

- ``grain``: ``second``, ``minute``, ``hour``, ``day``, ``week``, ``month``, ``quarter`` or
  ``year``. A ``date`` cannot take ``second``, ``minute`` or ``hour``; use ``datetime`` for
  those.
- ``fiscal_year_start``: the month number, 1 to 12, that the fiscal year starts in.

.. code-block:: yaml

   semantic_models:
     - name: orders
       dimensions:
         - name: order_month
           type: time
           type_params:
             time_granularity: month
           config:
             meta:
               s_layer:
                 value: {kind: date}
                 time: {grain: month, fiscal_year_start: 4}
                 display: {date_style: medium}

Step 4: State additivity (metrics only, when needed)
----------------------------------------------------

Add an ``aggregation`` section only when nothing upstream already says how the metric adds
up. It is allowed on metrics, not on facts or dimensions.

- ``additivity``: ``additive``, ``semi_additive`` or ``non_additive``.
- ``by``: the dimensions the metric must not be summed over. Required with
  ``semi_additive`` and not allowed otherwise.

A balance adds up across accounts but not across days:

.. code-block:: yaml

   metrics:
     - name: account_balance
       config:
         meta:
           s_layer:
             value: {kind: currency, currency: EUR}
             aggregation:
               additivity: semi_additive
               by: [balance_date]

.. note::

   ``percentage`` and ``score`` are already non-additive, so you do not need an
   ``aggregation`` section for them. If you write one, ``additivity`` must be
   ``non_additive``.

Step 5: Add a label, synonyms or extension keys (optional)
----------------------------------------------------------

- ``label``: a display name of 1 to 255 characters.
- ``synonyms``: a list of other names, each distinct and non-empty.
- ``x-<vendor>`` keys: any key that starts with ``x-``, holding any JSON value. The package
  keeps them as they are and does not interpret them. They are allowed at the top of the
  block and inside ``value``, ``display``, ``time`` and ``aggregation``.

.. code-block:: yaml

   metrics:
     - name: nps
       config:
         meta:
           s_layer:
             value: {kind: score, range: [-100, 100]}
             label: Net Promoter Score
             synonyms: [nps, promoter score]
             x-acme: {owner: customer-success}

.. note::

   Many platforms have their own label and synonyms fields. Whether ``label`` and
   ``synonyms`` belong in the block for your warehouse is decided by the tool that writes
   it, such as dbt-s-layer.

Step 6: Check the block
-----------------------

Save this as ``check_block.py``, paste your block between the triple quotes and set the
member type:

.. code-block:: python
   :caption: check_block.py

   import yaml

   from s_layer_semantic_formats import SLayerValidationError, validate_block

   block = yaml.safe_load("""
   value: {kind: currency, currency: EUR}
   aggregation:
     additivity: semi_additive
     by: [balance_date]
   """)

   try:
       validate_block(block, "metric")
   except SLayerValidationError as error:
       print(error)
   else:
       print("ok")

Run it:

.. code-block:: bash

   python check_block.py

A valid block prints:

.. code-block:: text

   ok

Otherwise the script prints every problem with the path of the key that caused it.

Troubleshooting
---------------

Each problem is reported as ``path: message``. The path is the key inside the block, such as
``display.decimals.max``.

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - Message
     - Fix
   * - ``unknown key; only 'x-' extension keys may be added``
     - The key is misspelled or in the wrong section. Only the keys in this guide and
       ``x-`` keys are allowed.
   * - ``Extra inputs are not permitted``
     - ``decimals`` and boolean ``labels`` take only their own keys, not ``x-`` keys. Move
       the extension key up to the enclosing section.
   * - ``unknown kind 'money'; expected one of: ...``
     - Use one of the kinds from Step 1.
   * - ``required key is missing``
     - Add the key named in the path, such as ``value.currency`` or ``value.unit``.
   * - ``kind 'currency' applies to a fact or metric, not a dimension``
     - The kind does not fit the member type. Pick a kind from Step 1 that does.
   * - ``not allowed on kind 'currency'``
     - The display or time key in the path does not fit the kind. See Steps 2 and 3.
   * - ``grain 'hour' is finer than a date; use kind datetime``
     - Use a ``day`` or coarser grain, or change the kind to ``datetime``.
   * - ``only allowed on a metric, not a fact``
     - Remove ``aggregation`` from facts and dimensions.
   * - ``required when additivity is semi_additive``
     - Add ``by`` with the dimensions the metric must not be summed over.
   * - ``kind 'percentage' implies non_additive``
     - Remove the ``aggregation`` section, or set ``additivity: non_additive``.
   * - ``Input should be a valid integer`` or ``Input should be a valid boolean``
     - Values are not converted. Write ``2``, not ``2.0`` or ``"2"``, and ``true``, not
       ``"yes"``.

.. tip::

   Problems with the shape of each key are reported first. Rules that compare sections, such
   as a ``display`` key that does not fit the kind, are checked once the shape is right, so
   fixing one round of problems can show a new one. Run the check again after each fix.

See also
--------

- :ref:`tutorial-first-blocks` walks through writing and checking blocks for the first time.
- :ref:`explanation-the-block` explains what each section is for.
- :ref:`explanation-design-decisions` lists every rule the package applies and why.
