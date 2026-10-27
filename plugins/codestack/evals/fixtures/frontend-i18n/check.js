// Evaluator-owned behavioral oracle. Keep outside every candidate workspace.
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');

const expected = {
    en: {
        title: 'Team members', label: 'Email address', placeholder: 'name@example.com',
        ariaLabel: 'Invite a team member', submit: 'Invite member', required: 'Enter an email address.',
        invalid: 'Enter a valid email address.', dialogTitle: 'Send invitation?',
        dialogBody: 'Invite {name} at {email}?', cancel: 'Cancel', confirm: 'Send invitation',
        toast: 'Invitation sent to {name} at {email}.'
    },
    'zh-CN': {
        title: '团队成员', label: '电子邮箱', placeholder: '姓名@example.com',
        ariaLabel: '邀请团队成员', submit: '邀请成员', required: '请输入电子邮箱。',
        invalid: '请输入有效的电子邮箱。', dialogTitle: '发送邀请？',
        dialogBody: '邀请 {name}（{email}）加入团队？', cancel: '取消', confirm: '发送邀请',
        toast: '已向 {name}（{email}）发送邀请。'
    }
};

function interpolate(template, values) {
    return template.replace(/\{(\w+)\}/g, (_match, key) => String(values[key]));
}

function check(workspace) {
    try {
        if (!fs.statSync(workspace).isDirectory()) throw new Error('Workspace must be a directory');
    } catch (error) {
        console.error(`Workspace unavailable (not behavioral RED): ${error.message}`);
        return 2;
    }
    let renderBoard, inviteMember;
    try {
        ({ renderBoard } = require(path.join(workspace, 'src/board.js')));
        ({ inviteMember } = require(path.join(workspace, 'src/invitation.js')));
        assert.equal(typeof renderBoard, 'function');
        assert.equal(typeof inviteMember, 'function');
    } catch (error) {
        // A supplied candidate that cannot load or preserve the API fails its contract.
        console.log(JSON.stringify({ functional: 'fail', passed: 0, total: 1,
            failures: [{ name: 'candidate module contract', detail: error.message }],
            organization: 'manual_review' }, null, 2));
        return 1;
    }
    const failures = [];
    let passed = 0;
    function verify(name, run) {
        try {
            run();
            passed += 1;
        } catch (error) {
            failures.push({ name, detail: error.message });
        }
    }
    const expectedMembers = [
        { id: 'user-9', name: 'Zoe 中文', status: 'invited' },
        { id: 'user-7', name: 'Ari 中文', status: 'active' }
    ];
    const freshMembers = () => expectedMembers.map(member => ({ ...member }));
    for (const [locale, copy] of Object.entries(expected)) {
        verify(`${locale}: existing title and business data`, () => {
            const members = freshMembers();
            const actual = renderBoard(locale, members);
            assert.deepEqual({ title: actual.title, members: actual.members }, { title: copy.title, members: expectedMembers });
            assert.deepEqual(members, expectedMembers);
        });
        verify(`${locale}: invitation presentation`, () => {
            assert.deepEqual(renderBoard(locale, freshMembers()).invite, {
                label: copy.label, placeholder: copy.placeholder, ariaLabel: copy.ariaLabel, submit: copy.submit
            });
        });
        verify(`${locale}: required validation`, () => {
            // Exercise the default, explicitly unconfirmed and confirmed paths.
            for (const confirmation of [[], [false], [true]]) {
                assert.deepEqual(inviteMember(locale, 'Ari 中文', '  ', ...confirmation), { ok: false, error: copy.required });
            }
        });
        verify(`${locale}: invalid email validation`, () => {
            for (const confirmation of [[], [false], [true]]) {
                assert.deepEqual(inviteMember(locale, 'Ari 中文', 'invalid', ...confirmation), { ok: false, error: copy.invalid });
            }
        });
        for (const person of [
            { name: 'Ari 中文', email: 'ari@example.com' },
            { name: 'Bo {email}', email: 'bo+test@example.org' }
        ]) {
            verify(`${locale}: successful action for ${person.email}`, () => {
                const result = {
                    ok: true, toast: interpolate(copy.toast, person),
                    payload: { ...person, status: 'invited' }
                };
                // Confirmation must use its current arguments, without prior pending data.
                assert.deepEqual(inviteMember(locale, person.name, ` ${person.email} `, true), result);
                inviteMember(locale, 'Other member', 'other@example.com');
                assert.deepEqual(inviteMember(locale, person.name, ` ${person.email} `, true), result);
            });
            verify(`${locale}: confirmation for ${person.email}`, () => {
                for (const confirmation of [[], [false]]) {
                    assert.deepEqual(inviteMember(locale, person.name, ` ${person.email} `, ...confirmation), {
                        ok: false,
                        confirmation: {
                            title: copy.dialogTitle, body: interpolate(copy.dialogBody, person),
                            cancel: copy.cancel, confirm: copy.confirm
                        }
                    });
                }
            });
        }
    }
    verify('input members remain unchanged', () => {
        for (const locale of Object.keys(expected)) {
            const members = freshMembers();
            renderBoard(locale, members);
            assert.deepEqual(members, expectedMembers);
        }
    });
    console.log(JSON.stringify({ functional: failures.length ? 'fail' : 'pass', passed,
        total: passed + failures.length, failures, organization: 'manual_review' }, null, 2));
    return failures.length ? 1 : 0;
}

if (require.main === module) {
    if (process.argv.length !== 3) {
        console.error('Usage: node check.js CANDIDATE_WORKSPACE');
        process.exitCode = 2;
    } else {
        process.exitCode = check(path.resolve(process.argv[2]));
    }
}

module.exports = { check };
