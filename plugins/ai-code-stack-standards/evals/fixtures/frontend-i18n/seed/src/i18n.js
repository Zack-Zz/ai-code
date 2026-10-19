const messages = {
    en: { title: 'Team members' },
    'zh-CN': { title: '团队成员' }
};

function t(locale, key, values = {}) {
    const template = messages[locale]?.[key];
    if (template === undefined) throw new Error(`Unknown message: ${locale}/${key}`);
    return template.replace(/\{(\w+)\}/g, (_match, name) => String(values[name]));
}

module.exports = { messages, t };
