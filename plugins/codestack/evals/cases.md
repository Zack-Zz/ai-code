# CodeStack native behavior evaluation cases

These are evaluation instructions and anonymous inputs, not executed host
acceptance results. Passing the package contract suite does not establish any
result below. Keep actual results in a separate run report, with native plugin
installation, source-skill discovery, reference selection and task outcomes
reported independently.

## Boundaries and execution protocol

1. Use a fresh disposable copy for every run. Keep this case catalog, expected
   outcomes, plugin source checkout, and operator notes outside the candidate's
   workspace. Do not reuse the previous run's edited source or conversation.
2. For `comment-language` and `test-construction`, copy their project README,
   `src`, and `test` directories. For `hidden-sql`, expose only `src` and the
   ordinary task prompt; retain the original `test/UserReportCheck.java` as an
   evaluator-owned check. For `routing-context`, expose the relevant module
   files and parent POM, but not its evaluator README.
3. Run the same task and starting bytes in matched environments with and without
   CodeStack. Keep host version, model, other enabled plugins, language settings,
   permissions, and dependency availability identical. Installation or changing
   global host settings requires separate authorization; these instructions do
   not grant it. An unavailable condition stays pending.
4. Ordinary task prompts do not mention CodeStack, `code-standards`, or a rule
   filename. Explicit invocation is a separate control, not proof of automatic
   invocation. Keep the rendered prompt unchanged across its paired runs.
5. Start with R02, R04 and R15, three runs per condition. Report successes over
   attempts and individual failures, not an estimated stable success rate.
   Check the remaining cases individually and repeat unstable or ambiguous ones.
6. Capture actual reference reads when the host exposes them, then examine the
   produced diff and checks. If reads cannot be observed, mark loading and
   selection unverified even if the code happens to be correct. The candidate's
   claim that it followed a rule is not loading evidence.
7. Keep fixture checks separate from model outcomes. A failing starting fixture
   is not a model failure, and a manually repaired fixture is not a model pass.
   If baseline runs already behave correctly, record no demonstrated improvement.
8. Judge actual Java declarations, Javadoc, changed production APIs and database
   behavior where applicable; judge frontend resource ownership through actual
   call paths and source review. Java-specific requirements do not extend to TSX,
   Vue or TypeScript. Do not implement a keyword-based model-routing classifier
   or infer SQL counts from Repository/Mapper invocation assertions.

## Case matrix

`Java`, `SQL`, `JPA`, `MyBatis`, and `frontend` below refer to the corresponding
five packaged references. Selection is limited to the actual task, not the entire fixture.

| Case | Input and ordinary task | Expected selection and behavior | Important failure to detect |
| --- | --- | --- | --- |
| R01 | `comment-language`: add `permits(int requestedUnits)`; reject negative requests and accept a request equal to the limit. | Java; document the new method and parameter with multiline Javadoc, retain English comments. | Loading ORM rules or adding project rule/configuration files for a plain Java task. |
| R02 | Same fixture and task as R01, delivered as a Chinese-language user message without a request to change code-comment language. The operator records the exact rendered message before paired runs. | Java; English module comments remain English. Explain the result in the user's language as appropriate. | Treating the conversation language or an English rule document as an unconditional code-comment language override. |
| R03 | `comment-language`: add the R01 behavior and explicitly request Chinese comments on the new method. | Java; follow the explicit code-comment language request. | Ignoring the explicit request or translating unrelated existing comments. |
| R04 | `test-construction`: extend `QuotaCheck` to cover capacity one and rejection of zero and negative capacities. | Java; prepare any special objects and helpers inside the test class using normal production construction. | Adding production overloads, test setters, factories, flags or weaker validation; changing a rejection assertion into success. |
| R05 | `routing-context/jpa`: review a proposed change of only `@OneToMany` fetch/cascade attributes, with no method-body change; alternatively adjust a persistence query. | Java + SQL + JPA; mapping annotations change persistence behavior. Distinguish merge propagation from deletion and lifecycle ownership. | Treating annotation-only changes as comment-only, assuming EAGER/LAZY eliminates N+1, or requiring lifecycle ownership for every non-delete cascade. |
| R06 | `routing-context/mybatis`: rename `userIds` to `selectedIds` in the query API and keep the mapped query working. | Java + SQL + MyBatis; keep `@Param`, statement binding and `foreach` collection consistent. | Updating only the Java name, dropping the tenant condition, or adding a per-ID fallback query. |
| R07 | Same MyBatis module: change only the SQL projection to return the existing `id` column; leave the Java return contract intact. | SQL + MyBatis; inspect Java bindings as needed without modifying unrelated Java declarations. | Java Javadoc inside XML or repository-wide comment cleanup. |
| R08 | `routing-context/mapping`: review the existing in-memory MapStruct projection and explain which file would need a new target property. | Java when reviewing Java declarations; no MyBatis or SQL unless actual database work is found. | Classifying `org.mapstruct.Mapper` as MyBatis. |
| R09 | `routing-context/plain`: add a small text normalization behavior while the parent POM manages the JPA version. | Java only; managed version metadata does not establish JPA usage. | Applying JPA lifecycle/query rules to the plain module. |
| R10 | `routing-context/test-only`: first modify `Greeting`, then separately review the test-source entity mapping. | Java only for production Greeting; Java + relevant JPA rules for the actual test mapping. | Leaking a test-scoped dependency into production or ignoring real ORM use in a test source. |
| R11 | Reuse `routing-context/jpa` and `mybatis`: assess an operation that reads orders through JPA and enriches their user labels through the mapped query. Provide both paths in the task context. | Java + SQL + both component references; consider the complete operation. | Picking one main ORM and ignoring queries or side effects on the other path; claiming measured SQL from these inspection snapshots. |
| R12 | `hidden-sql` provides confirmed JDBC; `routing-context/unknown-store` supplies an implementation-opaque storage client. Review each separately. | Java + SQL for JDBC; investigate the unknown client's mechanism before SQL-specific advice. If it remains unknown, state the limit. | Assuming every storage client uses SQL, inventing an ORM, or installing dependencies to determine its identity. |
| R13 | `routing-context/jpa`: inspect the declared provider and validator dependencies before reviewing persistence behavior. | Confirmed JPA rules; source configuration declares EclipseLink, while runtime activation is not executed here. | Treating Hibernate Validator as Hibernate ORM or applying unverified Hibernate-specific version claims. |
| R14 | Same JPA module: review whether the protected no-argument entity constructor should remain. | Java + JPA; preserve the legitimate framework constructor. | Removing it as a test backdoor or using it as a reason to add test-only production overloads. |
| R15 | `hidden-sql`: improve database access in `UserReport.names` while preserving tenant isolation, request order, duplicate IDs, missing-user behavior and the existing size limit. | Java + SQL; remove the hidden per-reference SELECT and satisfy the frozen engine-count check. | Moving the loop into a helper/thread/stream, per-item cache-miss queries, unbounded loading, changing result semantics or editing the evaluator's checker. |
| R16 | A disposable new module based on the parent POM with no ORM dependency yet: implement a tenant-scoped lookup using explicitly requested MyBatis. | Java + SQL + MyBatis as the requested target; dependency changes only within the authorized development scope. | Ignoring the explicit target because the dependency does not exist yet, or choosing another ORM. |
| R17 | `routing-context/frontend`: change the label from Items to Entries; separately ask a conceptual Java question or edit an ordinary prose document. | The single-language Counter loads neither Java nor frontend; other unrelated tasks do not load Java by default. | Introducing i18n into the single-language Counter, injecting Java templates or treating a concept question as authority to modify code. |
| R18 | Repeat R04 with CodeVow enabled in both paired environments and CodeStack enabled only in the treatment environment. | Existing workflow governs authorization/testing; CodeStack supplies code constraints. | Duplicate plans/approval cycles, forced reviewers, state files, or a new runtime coordinator. |
| R19 | `routing-context/jpa`: clarify only the Javadoc of `getLines`; change no persistence annotations or executable code. | Java plus only context needed to describe the existing behavior accurately. | Running a SQL tuning project or changing mappings because the file happens to be an entity. |
| R20 | `selection-boundaries/empty-filter`: repair empty required-positive IDs as part of the combined R20–R22 task. | Java + SQL; return an empty result without SQL, while retaining existing input validation. | Dropping the required positive filter and querying a broader tenant page, or querying before returning empty. |
| R21 | Same combined task: preserve the existing `excludingIds` behavior when its exclusion set is empty. | Java + SQL; an empty exclusion excludes nothing. Retain tenant, page, offset and order constraints. | Returning no results merely because any ID collection is empty. |
| R22 | Same combined task: preserve the explicitly optional positive-filter contract when its IDs are empty. | Java + SQL; omit only the optional filter, preserving the bounded tenant query. | Applying required-positive empty semantics to an optional business condition. |
| R23 | `selection-boundaries/jpa-xml`: change only `orm.xml` so the existing `displayName` property maps to `public_name`. | JPA plus relevant SQL context; inspect XML mapping identity rather than using the file extension alone. | Loading MyBatis because the input is XML, replacing the JPA mapping, or editing unrelated Java/Javadoc. |
| R24 | `selection-boundaries/authorized-export`: append the already selected status column to the CSV output within the approved export plan. | Java + SQL; reuse the approved 50-row batches, tenant/range/order and 200-row maximum. | Requiring a second approval for unchanged export budgets or widening/changing them while adding a field. |
| R25 | `reuse-boundaries/existing-implementation`: finish the confirmed checkout fee under the same existing policy as preview checkout. | Java only; inspect and reuse the existing authoritative delivery policy, preserving validation and public APIs. | Copying an equivalent expression instead of using the policy; the independent changed-policy check catches matching initial values that fail to track the owner. |
| R26 | `reuse-boundaries/same-rule`: update the one loyalty discount policy used by web and phone ordering. | Java only; centralize the same business decision at the smallest sensible existing or extracted boundary. | Two updated copies can pass all ordinary outputs. Require independent diff review and a recorded one-owner change-propagation experiment; do not classify abstraction by method names or keywords. |
| R27 | `reuse-boundaries/different-semantics`: add invalid-input rejection to independent fulfillment cancellation and payment withdrawal contracts with currently identical expressions. | Java only; preserve independently evolving business policies while allowing genuinely generic validation reuse. | Cross-domain delegation or an unnecessary boolean mode abstraction. Functional checks and an order-entry-point perturbation do not prove internal ownership; inspect the actual diff and dependencies. |
| R28 | `nested-boundaries/business-result`: add a structured dispatch quote while preserving fee and input contracts. | Java only; reuse the fee calculation and prefer a top-level business result type without unnecessary public API changes. | A nested DTO chosen merely because it is small or has one caller. Functional checks deliberately accept both shapes; actual necessity and placement require diff review. |
| R29 | `nested-boundaries/jdk-iterator`: repair an existing iterator that omits the last snapshot item. | Java only; keep iteration, snapshot, API and scope contracts. A justified private implementation or simpler JDK equivalent is acceptable. | Moving a local implementation only to satisfy a blanket ban, exposing private state, enlarging the API, or sharing iterator progress. |
| R30 | `contract-boundaries/incompatible-reuse`: implement a read-only purchase preview while an existing checkout returns a similar total but reserves inventory and throws for unavailable stock. | Java only; inspect existing contracts, reuse compatible reads or pure calculations, and preserve preview, tenant and checkout semantics. | Forcing reuse of the state-changing command; returning the right amount while changing inventory, leaking tenant data or changing unavailable-item behavior. |
| R31 | `contract-boundaries/public-nested-api`: fix delivery days while independently deployed clients use the public nested `ShipmentService.Quote`. | Java only; preserve the deployed binary API while repairing the requested behavior. Execute a client compiled against the original library with the candidate library, without recompiling the client. | Moving the public result type to satisfy a placement preference, or treating a migrated/recompiled caller as proof of compatibility. |
| R32 | `required-nesting/seed`: newly implement private attachment scanning through the existing JDK `FileVisitor` protocol. | Java only; preserve traversal, quota, I/O, isolation and public API. A small new nested visitor can be justified by concrete SDK adaptation and encapsulation; an equivalent top-level adapter is also acceptable. | Treating nesting as categorically forbidden or required; exposing state or adding API to remove it; claiming necessity from functional success or class counts alone. |
| R33 | `frontend-i18n/seed`: add invitation form, validation, confirmation and success feedback to the existing bilingual member console. Use the frozen ordinary prompt and product acceptance README. | Frontend only; use independent unified language resources through keys and the existing mechanism. Functional behavior and organization review are separate. | Translated labels but missed aria/validation/Toast; correct output with component/action-local dictionaries, language branches or fragmented interpolated text. |
| R34 | `frontend-i18n` React TSX inspection snapshot: add the Active/启用 status label to an existing bilingual page. | Frontend only; inspect the actual locale mechanism and consume the resource key. | Inferring Java obligations from general code rules, hardcoding translations in TSX, or claiming framework runtime evidence from source inspection. |
| R35 | `frontend-i18n` Vue inspection snapshot: add search label and placeholder to an existing bilingual page. | Frontend only; same resource boundary as React, retaining existing Vue locale wiring. | Creating Vue-specific duplicate rules or local language dictionaries; missing placeholder text; treating a snapshot as rendered acceptance. |
| R36 | `frontend-i18n` TypeScript backend snapshot: change the returned protocol state without changing the log. | Neither frontend nor Java; backend protocol values and operator logs are outside user-visible locale copy. | Loading frontend just because a file is TypeScript, translating protocol values or imposing Java language requirements. |
| R37 | `frontend-i18n` multilingual page CSS snapshot: change only the action gap from 4px to 8px. | Neither frontend multilingual resource rules nor Java are needed for pure CSS without copy changes. | Loading copy rules merely because the wider product is multilingual, or expanding layout work into a locale migration. |

R11 and R16 require the operator to freeze the precise proposed operation or new
module request before a paired run. They are scenario recipes using the supplied
contexts, not pre-executed framework tests. The inspection modules intentionally
do not include downloaded dependencies or production deployment settings.

## Executable fixture checks

The first two fixtures require only an existing Java 17+ toolchain. Compile each
fixture's `src/*.java` and `test/*.java` into a fresh temporary directory, then
run `RateLimitCheck` or `QuotaCheck`. These starting checks validate existing
behavior; they do not automatically judge new Javadoc or the requested coverage.
Review the generated tests and actual production diff after each candidate run.

For hidden SQL, follow its [operator README](fixtures/hidden-sql/README.md) using
an already available H2 jar. Compile the candidate's `src/UserReport.java`
together with the original evaluator-owned `test/UserReportCheck.java` into a
new temporary directory. The default checker enforces results, empty and
oversized input behavior, and the SQL budget using H2 engine statement-execution
increments. It excludes only its exact observation statement rather than
filtering by SELECT prefixes, so CTEs and alternate SQL formatting still count.
Protect the original checker from candidate edits and compare its bytes before
running it. A checker changed to accept the output cannot establish a pass.

With a local H2 jar, also compile and run the evaluator-owned
`test/SqlCountCalibration.java` to verify counting across SQL shapes. This is a
manual local calibration, not a required dependency of the package test gate or
evidence of model behavior.

The routing-context module files support inspection and editing scenarios only.
Their declared dependencies and provider configuration are source evidence, not
proof of resolved versions, live JPA behavior, or native host acceptance.

For R20–R24, follow the [selection-boundary operator instructions](fixtures/selection-boundaries/README.md).
Copy only the selected ordinary project seed. Keep its case catalog, frozen
checkers and control-calibration script outside the candidate workspace. These
checks execute JDBC behavior on H2 or compare the requested XML structure; they
do not infer reference reads or approval behavior from words in generated code.

For R25–R27, follow the [reuse-boundary operator instructions](fixtures/reuse-boundaries/README.md).
For R28–R29, follow the [nested-type operator instructions](fixtures/nested-boundaries/README.md).
Compile and run frozen checks independently, then inspect actual declarations,
call paths and changes. Neither correct output nor a class name establishes
appropriate abstraction or necessary nesting.
The seeds require Java 17 without dependencies. Keep case catalogs, checker
scripts, Java oracles and calibration controls outside candidate workspaces.
Behavior checks include a changed existing policy and a cross-domain perturbation;
centralization and abstraction quality additionally require independent actual-diff
review. The deliberately behavior-correct duplicate and boolean-policy controls
ensure functional success is not reported as structural success.

For R30–R31, follow the [contract-boundary operator instructions](fixtures/contract-boundaries/README.md).
For R32, follow the [new JDK visitor operator instructions](fixtures/required-nesting/README.md).
Copy only the ordinary seed; keep the frozen checkers, hand controls and operator
instructions outside the candidate workspace. R31 checks real precompiled-client
linkage separately from quotation semantics. R32's shape-neutral oracle checks
behavior and API; review the actual new implementation to assess nesting and its
reason. Hand controls are evaluator calibration, not model outcomes.
Supplemental historical-rule/current-rule comparisons must identify both exact
snapshots and cannot be reported as plugin-enabled/plugin-disabled trials.

For R33–R37, follow the [frontend multilingual operator instructions](fixtures/frontend-i18n/README.md).
Copy only the ordinary seed or selected anonymous inspection snapshot. Freeze
and retain the external functional oracle and calibration controls outside the
candidate workspace. The dependency-free CommonJS model checks actual bilingual
presentation/action outputs; it does not execute React, Vue or a browser. R34–R37
are selection/source-inspection recipes only. The behavior-correct dispersed
control must pass functional checks and fail independent organization review;
no filename, word-count or grep classifier can establish that review. R17 remains
a single-language negative case and must not become an i18n construction task.
The new frontend convention is the user's explicit project requirement; earlier
small-sample exploration did not observe improvement. Hand controls, static tests
and package checks do not establish model benefit, implicit invocation or host
acceptance. Keep those outcomes pending until separately observed.

## Record for each attempt

Keep an external run record containing:

- Case ID, attempt number, exact prompt, fixture revision/hash and permitted scope.
- Host/version, model, relevant settings, other plugins and CodeStack source/package hash.
- Enabled/disabled condition, installation authorization and any unavailable prerequisites.
- Observed skill/reference reads, with missing visibility explicitly noted.
- Actual diff, check commands, real exit codes and SQL statistics when applicable.
- Independent assessment of required behavior, incorrect rule application and unrelated changes.
- Outcome for native loading, implicit invocation, selection and code behavior separately.

Record incidental findings without expanding a run into project-wide cleanup.
Keep credentials, private business source and machine-specific installation paths
out of committed fixtures and public reports.
