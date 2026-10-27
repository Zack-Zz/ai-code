# Reuse and abstraction evaluation inputs

These small Java 17 projects exercise reuse of an existing implementation,
one business policy duplicated across entry points, and superficially identical
policies with different business ownership. They have no external dependencies.
Only the chosen seed's `README.md` and `src` directory enter a disposable model
workspace. Keep this README, `check.py`, `calibrate.py`, and `oracle` outside it.
They are evaluator tools, outside the plugin package allowlist and uniform gate.

## Frozen ordinary tasks

Record the exact rendered prompt before a matched run. It may be translated to
the conversation language, but must not change between the old-rule and new-rule
conditions. Do not name the plugin, reference file, or evaluation case in an
ordinary task. The seed READMEs describe actual domain ownership rather than
operator expectations.

| Case | Seed and ordinary task | Permitted source scope |
| --- | --- | --- |
| R25 | `existing-implementation`: finish `Checkout.confirmedFee` so confirmed and preview checkout follow the same delivery policy described in README. Retain negative-subtotal rejection and public APIs. The implementation plan is approved; complete and compile the change with Java 17, without installing dependencies or operating Git. | Only `src/Checkout.java`; retain the authoritative `DeliveryFees` implementation and README bytes. |
| R26 | `same-rule`: the business approved one loyalty discount policy for `WebOrders` and `PhoneOrders`: loyalty members receive 700 cents at subtotals of at least 15000 cents, otherwise zero. Nonmembers still receive zero and negative subtotals remain invalid. Retain both public APIs. The plan is approved; complete and compile the change with Java 17, without installing dependencies or operating Git. | Modify or add necessary Java files under `src`; retain README and both public entry points. Do not prescribe a helper name, number of classes, or particular abstraction in the prompt. |
| R27 | `different-semantics`: repair invalid-input handling in `OrderCancellation.canCancel` and `RefundWithdrawal.canWithdraw`: null status or negative elapsed minutes must throw `IllegalArgumentException`. Legal inputs must continue to follow the separate existing business contracts in README. Retain public APIs. The plan is approved; complete and compile the change with Java 17, without installing dependencies or operating Git. | Modify or add necessary Java files under `src`; retain README and both public entry points. |

Compile output belongs in an external temporary directory, not in the candidate
source tree. A separately staged native `.agents` skill subtree is evaluation
setup, never candidate-editable configuration. Compare its bytes against staging
and inspect actual read events independently; a passing Java check cannot prove
the skill or correct references were selected.

## Behavior and structure are separate judgments

```sh
python3 -B <evaluator>/check.py existing-implementation <candidate>
python3 -B <evaluator>/check.py same-rule <candidate>
python3 -B <evaluator>/check.py different-semantics <candidate>
```

Freeze the checker and seed bytes before running a model. The checker uses
fresh temporary class directories and evaluator-owned Java checks rather than
accepting candidate-written tests. It checks permitted file scope, boundary
values, invalid-input exceptions and both public entry points.

For R25, it also copies the candidate and changes only the immutable existing
`DeliveryFees` policy: the threshold becomes 9000, fees become 317 and 29 cents.
Both checkout entry points must pick up the changed policy. A copied expression
that merely produced the same initial values fails this perturbation. This
establishes use of the existing policy for the checked inputs; inspect the diff
for unnecessary wrappers, unrelated changes and preserved contracts as well.

For R26, correct outputs alone do not establish centralized ownership. An
independent reviewer must trace both entry points in the actual diff, identify
the one owner of the loyalty decision, and judge whether the extraction is the
smallest sensible boundary. One small domain policy with two direct calls is a
valid solution; a generic strategy framework, speculative extension points or
two updated copies are not justified by this seed. No specific helper identifier
is required and keyword counts are not an abstraction judgment.

After the reviewer identifies the actual owner, make a separate evaluator copy,
record a diff that changes its discount amount once from 700 to 1100, and run:

```sh
python3 -B <evaluator>/check.py same-rule <one-owner-change-copy> --discount 1100
```

Both entry points must change together. Record the selected edit and results;
the check does not discover the owner or prove general change propagation.
Do not modify the candidate's recorded output when performing this experiment.

For R27, the checker separately substitutes an order entry point that rejects
all cancellation, then verifies refund behavior remains unchanged. This catches
refund delegation through that public order method. It does not establish that
there is no shared internal policy: a boolean-dispatched common business method
can pass every functional check while still coupling independent owners.
An independent reviewer must therefore inspect actual dependencies and policy
placement. Keep the fulfillment and settlement decisions independent; do not
combine them solely because their current expressions match. Reusing genuinely
generic validation or existing well-scoped utilities is allowed when neither
domain policy depends on the other's lifecycle or future changes. Ordinary
boolean business data, such as `loyaltyMember` in R26, is not an abstraction defect.

For all cases, also judge multiline Javadoc, argument documentation, test-only
production backdoors, and changes outside the task. Record functional behavior,
structural appropriateness, reference reads, and host loading separately. A
model's claim of reuse is not evidence of reuse.

## Calibrate the checks with explicit controls

```sh
python3 -B <evaluator>/calibrate.py
```

The script preserves real commands, exit codes and assertion output in a fresh
external temporary directory. It exercises these known controls:

| Control | Expected behavior check | Required independent structural judgment |
| --- | --- | --- |
| R25 unfinished entry point | Fail: confirmed checkout does not return a fee | Starting defect, never a model outcome. |
| R25 direct existing-policy delegation | Pass original and changed policies | Accept the existing owner without a new framework. |
| R25 matching-value copied calculation | Original values pass; changed policy fails | Reject duplication even though initial outputs matched. |
| R26 old duplicated policy | Fail the approved policy behavior | Starting defect. |
| R26 two updated copies | Pass ordinary behavior | Reject after inspecting the two independently owned decisions. A behavior pass is deliberately insufficient. |
| R26 one of the two copies changed to 1100 | Fail the changed-policy check | Demonstrates this explicit duplicate's missed propagation. |
| R26 small extracted policy | Pass ordinary behavior | Accept after inspecting the one shared business owner and direct calls. |
| R26 extracted owner changed once to 1100 | Pass the changed-policy check | Record the single physical edit and both outputs. |
| R27 missing input validation | Fail invalid-input rejection | Starting defect. |
| R27 independently owned policies | Pass behavior and order perturbation | Accept the deliberate policy separation. |
| R27 refund delegates to order policy | Original behavior passes; order perturbation fails | Reject cross-domain ownership. |
| R27 unnecessary boolean common business method | Pass behavior and order perturbation | Reject after diff review. This is a negative structural control intentionally outside automatic classification. |

The JSON records structural **expectations**, not computed structural verdicts.
Review the explicit control code independently and record actual judgments in the
run report. A passing calibration establishes only these checker properties.
It does not mean a model reused code, chose an appropriate abstraction, selected
the Java rules, or improved relative to the old rules. Handwritten positive
controls never count as model successes. If both matched native conditions are
already correct, report no demonstrated improvement.
