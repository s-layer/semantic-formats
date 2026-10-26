.. meta::
   :description: Background on the s_layer block, its normal form and the rules the package applies

.. _explanation:

Explanation
===========

These pages explain why the vocabulary works the way it does. Read them when a rule
surprises you, or before you build a tool on top of the package.

- :ref:`explanation-the-block` -- What a block describes, how its sections divide the work
  and how a block travels from dbt YAML to a warehouse and back.
- :ref:`explanation-normal-form` -- Which defaults are filled in, how equality works and how
  the ``S_LAYER_SPEC`` payload derives from the normal form.
- :ref:`explanation-design-decisions` -- The rules the package applies where the design doc
  is silent, grouped by theme.

.. toctree::
   :hidden:

   the-block
   normal-form
   design-decisions
