
# About this Document

This document introduces and details the Quantum Orchestration Platform (QOP) programming environment.
It is intended for quantum developers and researchers working with the QOP.

## Shields

As more and more hardware products and QUA features are joining the QM arsenal, the documentation grows and branches out.
Keeping our documentation under a single (virtual) roof means that some of the features documented here are only applicable
for specific combinations of hardware and software.

To keep track of these specifications we introduce the usage of `shields`.

- Blue shields specify the required hardware and QOP version.
- Green shields indicate the required minimal version of QUA.
- Orange shields indicate required hardware add-ons, such as Octave.

For example, a feature that only works on an OPX+ with QOP version >2.0, with the Octave add-on, and requires QUA version >0.3.3 will have these shields:
{{ requirement("OPX+", "2.0.0") }}
{{ requirement("QUA", "0.3.3") }}
{{ requirement("Octave") }}
