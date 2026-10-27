const { t } = require('./i18n');

function renderBoard(locale, members) {
    return { title: t(locale, 'title'), members: members.map(member => ({ ...member })) };
}

module.exports = { renderBoard };
