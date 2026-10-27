// Hand-authored calibration controls, never model outcomes or an organization scorer.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const copies = {
    en: {
        label: 'Email address', placeholder: 'name@example.com', ariaLabel: 'Invite a team member',
        submit: 'Invite member', required: 'Enter an email address.', invalid: 'Enter a valid email address.',
        dialogTitle: 'Send invitation?', dialogBody: 'Invite {name} at {email}?',
        cancel: 'Cancel', confirm: 'Send invitation', toast: 'Invitation sent to {name} at {email}.'
    },
    'zh-CN': {
        label: '电子邮箱', placeholder: '姓名@example.com', ariaLabel: '邀请团队成员', submit: '邀请成员',
        required: '请输入电子邮箱。', invalid: '请输入有效的电子邮箱。', dialogTitle: '发送邀请？',
        dialogBody: '邀请 {name}（{email}）加入团队？', cancel: '取消', confirm: '发送邀请',
        toast: '已向 {name}（{email}）发送邀请。'
    }
};

const viewBody = `function renderBoard(locale, members) {
    return {
        title: t(locale, 'title'), members: members.map(member => ({ ...member })),
        invite: {
            label: lookup(locale, 'label'), placeholder: lookup(locale, 'placeholder'),
            ariaLabel: lookup(locale, 'ariaLabel'), submit: lookup(locale, 'submit')
        }
    };
}
module.exports = { renderBoard };
`;

const actionBody = `function inviteMember(locale, name, email, confirmed = false) {
    email = email.trim();
    if (!email) return { ok: false, error: lookup(locale, 'required') };
    if (!/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(email)) {
        return { ok: false, error: lookup(locale, 'invalid') };
    }
    const values = { name, email };
    if (!confirmed) {
        return { ok: false, confirmation: {
            title: lookup(locale, 'dialogTitle'), body: lookup(locale, 'dialogBody', values),
            cancel: lookup(locale, 'cancel'), confirm: lookup(locale, 'confirm')
        } };
    }
    return { ok: true, toast: lookup(locale, 'toast', values), payload: { name, email, status: 'invited' } };
}
module.exports = { inviteMember };
`;

function write(project, file, content) {
    fs.writeFileSync(path.join(project, 'src', file), content);
}

function centralized(project) {
    // Extend the existing authoritative locale resource, preserving its lookup mechanism.
    const original = fs.readFileSync(path.join(project, 'src/i18n.js'), 'utf8');
    const resources = {
        en: { title: 'Team members', ...copies.en },
        'zh-CN': { title: '团队成员', ...copies['zh-CN'] }
    };
    const lookup = original.slice(original.indexOf('function t('));
    write(project, 'i18n.js', `const messages = ${JSON.stringify(resources, null, 4)};\n\n${lookup}`);
    write(project, 'board.js', `const { t } = require('./i18n');\nconst lookup = t;\n\n${viewBody}`);
    write(project, 'invitation.js', `const { t: lookup } = require('./i18n');\n\n${actionBody}`);
}

function localDictionary(keys) {
    const resources = Object.fromEntries(Object.entries(copies).map(([locale, messages]) => [
        locale, Object.fromEntries(keys.map(key => [key, messages[key]]))
    ]));
    return `const localCopy = ${JSON.stringify(resources, null, 4)};
function lookup(locale, key, values = {}) {
    return localCopy[locale][key].replace(/\\{(\\w+)\\}/g, (_match, name) => String(values[name]));
}
\n`;
}

function dispersed(project) {
    // Behavior-correct translations live separately in UI and action modules.
    write(project, 'board.js', `const { t } = require('./i18n');\n${localDictionary([
        'label', 'placeholder', 'ariaLabel', 'submit'
    ])}${viewBody}`);
    write(project, 'invitation.js', localDictionary([
        'required', 'invalid', 'dialogTitle', 'dialogBody', 'cancel', 'confirm', 'toast'
    ]) + actionBody);
}

function untranslated(project) {
    centralized(project);
    const file = path.join(project, 'src/i18n.js');
    const content = fs.readFileSync(file, 'utf8');
    assert.ok(content.includes(copies['zh-CN'].toast));
    fs.writeFileSync(file, content.replace(copies['zh-CN'].toast, copies.en.toast));
}

function replaceSource(project, file, before, after) {
    const original = fs.readFileSync(path.join(project, 'src', file), 'utf8');
    assert.ok(original.includes(before), `${file}: control must actually change its target`);
    write(project, file, original.replace(before, after));
}

function validationAfterConfirmation(project) {
    centralized(project);
    replaceSource(project, 'invitation.js', 'if (!email)', 'if (confirmed && !email)');
    replaceSource(project, 'invitation.js', 'if (!/', 'if (confirmed && !/');
}

function mutatingMemberOrder(project) {
    centralized(project);
    replaceSource(project, 'board.js', 'members.map(',
        'members.sort((left, right) => left.name.localeCompare(right.name)).map(');
}

function sequenceDependentConfirmation(project) {
    centralized(project);
    replaceSource(project, 'invitation.js', 'function inviteMember(', 'let pending;\n\nfunction inviteMember(');
    replaceSource(project, 'invitation.js', '    const values = { name, email };',
        '    if (confirmed) ({ name, email } = pending);\n    else pending = { name, email };\n    const values = { name, email };');
}

function explicitFalseBypassesConfirmation(project) {
    centralized(project);
    replaceSource(project, 'invitation.js', 'confirmed = false', 'confirmed');
    replaceSource(project, 'invitation.js', 'if (!confirmed)', 'if (confirmed === undefined)');
}

function runControl(root, name, mutate, expectedExit, expectedPassed, expectedTotal = 17) {
    const project = path.join(root, name);
    fs.cpSync(path.join(__dirname, 'seed'), project, { recursive: true });
    mutate(project);
    for (const file of fs.readdirSync(path.join(project, 'src'))) {
        if (!file.endsWith('.js')) continue;
        const syntax = spawnSync(process.execPath, ['--check', path.join(project, 'src', file)], { encoding: 'utf8' });
        assert.equal(syntax.status, 0, `${name}: syntax/environment error\n${syntax.stderr}`);
    }
    const result = spawnSync(process.execPath, [path.join(__dirname, 'check.js'), project], { encoding: 'utf8' });
    assert.equal(result.status, expectedExit, `${name}: unexpected check exit\n${result.stdout}\n${result.stderr}`);
    const report = JSON.parse(result.stdout);
    assert.equal(report.passed, expectedPassed, `${name}: unexpected functional coverage`);
    assert.equal(report.total, expectedTotal);
    assert.equal(report.organization, 'manual_review');
    if (name === 'missing-translation') {
        assert.deepEqual(report.failures.map(failure => failure.name), [
            'zh-CN: successful action for ari@example.com',
            'zh-CN: successful action for bo+test@example.org'
        ]);
    }
    if (name === 'validation-after-confirmation') {
        assert.deepEqual(report.failures.map(failure => failure.name), [
            'en: required validation', 'en: invalid email validation',
            'zh-CN: required validation', 'zh-CN: invalid email validation'
        ]);
    }
    if (name === 'mutating-member-order') {
        assert.deepEqual(report.failures.map(failure => failure.name), [
            'en: existing title and business data', 'zh-CN: existing title and business data',
            'input members remain unchanged'
        ]);
    }
    if (name === 'sequence-dependent-confirmation') {
        assert.deepEqual(report.failures.map(failure => failure.name), [
            'en: successful action for ari@example.com', 'en: successful action for bo+test@example.org',
            'zh-CN: successful action for ari@example.com', 'zh-CN: successful action for bo+test@example.org'
        ]);
    }
    if (name === 'explicit-false-bypasses-confirmation') {
        assert.deepEqual(report.failures.map(failure => failure.name), [
            'en: confirmation for ari@example.com', 'en: confirmation for bo+test@example.org',
            'zh-CN: confirmation for ari@example.com', 'zh-CN: confirmation for bo+test@example.org'
        ]);
    }
    console.log(`${name}: exit ${result.status}, ${report.passed}/${report.total} functional; organization unscored`);
}

const outputIndex = process.argv.indexOf('--output');
if (process.argv.length !== 2 && (process.argv.length !== 4 || outputIndex !== 2)) {
    throw new Error('Usage: node calibrate.js [--output NEW_EXTERNAL_DIRECTORY]');
}
const keep = outputIndex !== -1;
const root = keep ? path.resolve(process.argv[3]) : fs.mkdtempSync(path.join(os.tmpdir(), 'codestack-i18n-'));
if (keep) fs.mkdirSync(root); // Must not overwrite a pre-existing directory.
try {
    runControl(root, 'seed', () => {}, 1, 3);
    runControl(root, 'centralized', centralized, 0, 17);
    runControl(root, 'dispersed', dispersed, 0, 17);
    runControl(root, 'missing-translation', untranslated, 1, 15);
    runControl(root, 'broken-export', project => write(project, 'invitation.js', 'module.exports = {};\n'), 1, 0, 1);
    runControl(root, 'validation-after-confirmation', validationAfterConfirmation, 1, 13);
    runControl(root, 'mutating-member-order', mutatingMemberOrder, 1, 14);
    runControl(root, 'sequence-dependent-confirmation', sequenceDependentConfirmation, 1, 13);
    runControl(root, 'explicit-false-bypasses-confirmation', explicitFalseBypassesConfirmation, 1, 13);
    console.log('9 hand-control outcomes matched; no model, reference selection, or organization score was inferred.');
    if (keep) console.log(`Inspect generated controls at ${root}; no report file was generated.`);
} finally {
    if (!keep) fs.rmSync(root, { recursive: true, force: true });
}
