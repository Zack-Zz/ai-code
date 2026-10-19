# Frontend multilingual boundary evaluation — operator guide

Internal evaluation material, outside the plugin's runtime resource allowlist.
These anonymous inputs exercise an explicitly requested project convention.
Earlier small-sample exploration did not demonstrate improvement; adopting the
convention is not a claim of measured model benefit. No native-host or framework
acceptance is recorded here.

## R33: an ordinary feature in an existing bilingual product

Copy **only `seed/`** to a fresh disposable candidate workspace. Keep this guide,
`check.js`, `calibrate.js`, the case catalog and plugin source outside it. The
seed README is ordinary product acceptance material: it mentions the shipped
languages and approved copy without telling the candidate how to organize them.
Freeze seed/checker bytes and the exact prompt before paired runs. Record SHA-256
hashes externally; recheck the frozen checker before executing candidate output.
Never run a candidate-edited copy of the oracle as evaluation evidence.

Use this ordinary prompt unchanged in both conditions:

> 请完成成员页面的邀请功能，满足 README 中的呈现、校验、确认和成功反馈约定，保留现有列表行为。实现方案已确认，请直接修改或新增 src 下的文件并用 Node.js 验证；不要修改 README、安装依赖、发送真实邀请或操作 Git。

From the repository root, using an already available Node.js 22+ runtime:

```sh
node plugins/ai-code-stack-standards/evals/fixtures/frontend-i18n/check.js /private/tmp/CANDIDATE
node plugins/ai-code-stack-standards/evals/fixtures/frontend-i18n/calibrate.js
```

The seed is valid executable CommonJS. The functional oracle exits **1** with
3/17 checks passing: existing title/data checks pass while the unimplemented
invitation behavior fails. Exit **2** denotes invalid invocation or an unavailable workspace and cannot
count as behavioral RED. Candidate syntax errors, missing modules and broken
exports in an existing workspace instead fail the module contract with exit **1**
and a separate 0/1 result; they are not mislabeled as environment trouble.
The oracle checks both locales, visible form text, placeholder, accessible name,
validation before default/explicit confirmation, dialog buttons/body for both
omitted and explicitly false confirmation arguments in both locales and for both
users, success Toast, full interpolated templates, email trimming, literal placeholder-like
business data and retained protocol data. A successful action is exercised before
requesting its confirmation and after a different user's confirmation; it must
use its own arguments rather than hidden pending data. Member preservation uses
fresh, nonalphabetical multi-member inputs and independent expected data, so an
in-place sort cannot change both the input and its expected result unnoticed.
It accepts behavior-correct centralized and dispersed implementations equally.
There is no source parsing, word count, grep, filename or directory-name score.

Report functional result (`passed/17`, exit code and failed assertions) separately
from organization review (`pass`, `fail`, or `insufficient evidence`). The latter
requires inspecting the **actual candidate source and diff**:

1. Trace each changed user-visible surface from its UI/action call site to its
   owned language resource and key. Include validation, accessibility and the
   complete interpolated dialog/Toast sentences, not just labels.
2. Establish that the translations belong to one independent, unified resource
   area and are consumed through keys using the existing mechanism. Splitting
   resources by locale or domain is acceptable. No particular directory name,
   file count or library is required; judge ownership and dependency direction.
3. Check that components/actions have not created their own dictionaries,
   language-conditional copies or hardcoded translations. Do not misclassify
   dynamic business names, protocol status values or diagnostic logs as copy.
4. Record concrete paths/symbols and any omission. Do not require a new i18n
   library, translate a single-language product, or migrate unrelated old code.

Keep that trace table and decision in the external run record. Correct strings
alone cannot establish resource organization. An evaluator must not turn the
above checklist into a keyword-based source classifier.

## Hand-control calibration

`calibrate.js` generates fresh temporary copies and uses the frozen oracle in
separate Node processes. It checks syntax first and removes its temporary source
on completion. The plugin test runner and repository `npm test` also run this
calibration; that checks the authored oracle controls, not model behavior or
native selection. To inspect the actual generated call paths, retain controls in a
new **external** directory (must not exist):

```sh
node plugins/ai-code-stack-standards/evals/fixtures/frontend-i18n/calibrate.js --output /private/tmp/NEW_CONTROLS
```

No generated report belongs in source control. Hand-control results are neither
model successes nor model failures and do not demonstrate automatic selection.

| Control | Expected functional outcome | Organization review expectation, to verify manually |
| --- | --- | --- |
| `seed` | exit 1; 3/17 | New behavior absent; no candidate organization judgment. |
| `centralized` | exit 0; 17/17 | Pass: `centralized()` extends `i18n.js`'s `messages`; `renderBoard()` and `inviteMember()` reach the existing `t()` by key, including complete templates. |
| `dispersed` | exit 0; 17/17 | Fail: `dispersed()` leaves the title resource but gives `board.js` and `invitation.js` separate `localCopy` dictionaries and local lookups. Full translation coverage does not repair ownership. |
| `missing-translation` | exit 1; 15/17 | Centralized organization still requires source review; Chinese success Toast falls back to English in two exercised inputs. Functional failure is distinct. |
| `broken-export` | exit 1; 0/1 module contract | A syntactically valid candidate removes the action export. This is a candidate failure, not an unavailable runtime. |
| `validation-after-confirmation` | exit 1; 13/17 | Central resources remain, but empty/invalid email is checked only when already confirmed. Default and explicit unconfirmed calls incorrectly return dialogs. |
| `mutating-member-order` | exit 1; 14/17 | Central resources remain, but `renderBoard()` sorts the input members in place. Independent input/output snapshots detect the regression. |
| `sequence-dependent-confirmation` | exit 1; 13/17 | Central resources remain, but confirmed actions reuse a module-level pending user. Direct and interleaved calls must use the supplied user instead. |
| `explicit-false-bypasses-confirmation` | exit 1; 13/17 | Central resources remain, but valid calls return a dialog only when the fourth argument is omitted. Explicit `false` must also require confirmation for both users and locales. |

The script asserts only functional outcomes and leaves `organization` as
`manual_review`. The control labels document author intent, not an algorithmic
organization score. Inspect the generated source before using these controls to
calibrate a reviewer.

## R34–R37: frozen selection snapshots

These are source-inspection tasks, not installed framework projects. Copy only
one snapshot's ordinary project notes and source blocks into a new workspace,
using the indicated relative paths; omit headings, expected selections and this
operator guide. Preserve the exact file bytes and prompt per condition. Observe
actual skill/reference reads if available. Without observable reads, selection
stays unverified even if the proposed patch looks correct. Do not install the
listed frameworks or claim TSX/Vue/browser runtime checks from these snapshots.

### R34 — existing React TSX product

Ordinary `README.md`: “The member page ships in English and Simplified Chinese.
React and TypeScript are already part of the product; dependencies are omitted
from this inspection snapshot. The locale adapter supplies `t` to the page.”

`src/Members.tsx`:

```tsx
type Props = { t: (key: string) => string; count: number };
export function Members({ t, count }: Props) {
  return <section><h1>{t('members.title')}</h1><span>{count}</span></section>;
}
```

`src/copy.ts`:

```ts
export const copy = {
  en: { 'members.title': 'Team members' },
  'zh-CN': { 'members.title': '团队成员' }
};
```

Frozen ordinary prompt:

> 在成员页数量旁新增“Active”状态标签，中文显示“启用”。只修改该页面及其直接支持文件；方案已确认，请直接完成，不要安装依赖或操作 Git。

Expected: frontend only; inspect existing locale wiring and use its resources.
No Java rules or Java Javadoc/test-construction obligations on TSX. Treat the
count as business data. A label hardcoded in TSX or a local locale branch is a
semantic organization failure regardless of whether a static snapshot renders.

### R35 — existing Vue product

Ordinary `README.md`: “This Vue member screen already supports `en` and `zh-CN`
through the existing `useI18n` adapter. Dependencies are omitted from this
inspection snapshot.”

`src/Members.vue`:

```vue
<script setup lang="ts">
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
</script>
<template><h1>{{ t('members.title') }}</h1></template>
```

`src/copy.ts`: use the exact `src/copy.ts` block from R34.

Frozen ordinary prompt:

> 在成员标题后增加一个搜索框，标签为“Search members”/“搜索成员”，占位符为“Name or email”/“姓名或邮箱”。只修改该页面及其直接支持文件；方案已确认，请直接完成，不要安装依赖或操作 Git。

Expected: frontend only with the same resource rule as React; preserve the
existing mechanism. Verify labels and placeholders by source inspection. The
snapshot is not evidence of resolved Vue dependencies, rendering or accessibility
acceptance in a browser.

### R36 — TypeScript backend

Ordinary `README.md`: “This is a Node HTTP service with no frontend or user-facing
localized copy. `state` is a protocol value and the message is an operator log.”

`src/state.ts`:

```ts
export function state(id: string) {
  console.info('state requested', id);
  return { id, state: 'ready' };
}
```

Frozen ordinary prompt:

> 将 state 的协议返回值从 ready 改为 available，保持 id 和运维日志不变。方案已确认，请直接完成，不要安装依赖或操作 Git。

Expected: neither frontend nor Java references; do not create locale resources
for a backend protocol value or log. TypeScript alone does not imply frontend.

### R37 — CSS-only work in a multilingual product

Ordinary `README.md`: “This existing member page ships in English and Simplified
Chinese. The requested change concerns only layout; visible copy is unchanged.”

`src/member.css`:

```css
.member-actions { display: flex; gap: 4px; }
```

Frozen ordinary prompt:

> 仅把 member-actions 的按钮间距调整为 8px，不改文案和其他文件。方案已确认，请直接完成，不要安装依赖或操作 Git。

Expected: no frontend multilingual resource reference is needed for this task;
no Java references. Existing multilingual product identity alone does not turn
pure styling into copy work. Check the bounded diff, not a framework runtime.

R17 remains the separate existing **single-language** Counter negative control.
Change only its Items label to Entries; do not introduce i18n or load frontend
multilingual/Java references. It is not a request to build multilingual support.
