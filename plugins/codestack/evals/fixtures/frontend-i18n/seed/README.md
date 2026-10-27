# Member console

This is the dependency-free presentation/action model of a small member console.
The shipped product supports English (`en`) and Simplified Chinese (`zh-CN`).
Its existing member list and page title work; the invitation action currently
returns `unavailable`. Node.js 22+ is sufficient. Do not install dependencies.

Implement the invitation form and action without changing the exported APIs:

- `renderBoard(locale, members)` retains `title` and the unmodified member data,
  and adds `invite: { label, placeholder, ariaLabel, submit }`.
- `inviteMember(locale, name, email, confirmed = false)` trims the email. An empty
  or invalid address returns `{ ok: false, error }` before any confirmation.
  Accept ordinary addresses such as `ari@example.com` and `bo+test@example.org`;
  reject `invalid`. Do not change the supplied display name or translate member
  names, email addresses, IDs, or protocol status values.
- A valid unconfirmed action returns `{ ok: false, confirmation: { title, body,
  cancel, confirm } }`. A confirmed action returns `{ ok: true, toast, payload:
  { name, email, status: 'invited' } }`. This is a pure local model: do not send
  email or add network calls, persistence or a browser framework.
- Substitute the name and trimmed email into the complete sentences below.
  A name may itself contain text such as `Bo {email}`; retain that text literally.

Approved visible copy:

| Surface | English | Simplified Chinese |
| --- | --- | --- |
| Existing title | Team members | 团队成员 |
| Email label | Email address | 电子邮箱 |
| Placeholder | `name@example.com` | `姓名@example.com` |
| Accessible form name | Invite a team member | 邀请团队成员 |
| Submit button | Invite member | 邀请成员 |
| Required validation | Enter an email address. | 请输入电子邮箱。 |
| Invalid validation | Enter a valid email address. | 请输入有效的电子邮箱。 |
| Dialog title | Send invitation? | 发送邀请？ |
| Dialog body | Invite {name} at {email}? | 邀请 {name}（{email}）加入团队？ |
| Cancel button | Cancel | 取消 |
| Confirm button | Send invitation | 发送邀请 |
| Success Toast | Invitation sent to {name} at {email}. | 已向 {name}（{email}）发送邀请。 |

Only `src/` may be changed or extended. Keep the CommonJS APIs and existing
behavior. Check JavaScript syntax and exercise the model with Node.js; no React,
Vue or browser execution is required by this project snapshot.
