const js = require('@eslint/js');
const globals = require('globals');

module.exports = [
    {
        ignores: ['node_modules/**', 'plugins/reed/prototype/dist/**', 'plugins/reed/prototype/.evidence/**']
    },
    js.configs.recommended,
    {
        languageOptions: {
            ecmaVersion: 2022,
            sourceType: 'commonjs',
            globals: {
                ...globals.node,
                ...globals.es2022
            }
        },
        rules: {
            'no-unused-vars': ['error', {
                argsIgnorePattern: '^_',
                varsIgnorePattern: '^_',
                caughtErrorsIgnorePattern: '^_'
            }],
            'no-undef': 'error',
            'eqeqeq': 'warn'
        }
    },
    {
        files: ['plugins/*/adapters/dsh/**/*.js', 'plugins/*/tests/dsh/**/*.mjs', 'published/dsh/**/*.js'],
        languageOptions: { sourceType: 'module' }
    },
    {
        files: ['plugins/reed/prototype/**/*.js', 'plugins/reed/prototype/**/*.mjs'],
        languageOptions: { sourceType: 'module' }
    }
];
