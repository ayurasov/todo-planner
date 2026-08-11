import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import globals from 'globals'

export default [
  {
    ignores: ['dist/**', 'node_modules/**', 'backend/**'],
  },
  js.configs.recommended,
  ...pluginVue.configs['flat/essential'],
  {
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    rules: {
      // Минимальный конфиг (Промпт 21): приоритет — поймать явные баги
      // (unused vars, undefined vars), а не стилистика.
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      // Ложные срабатывания на деструктуризации в <script setup> (известная
      // проблема взаимодействия eslint core-парсера с vue-parser) -- отключено.
      'no-useless-assignment': 'off',
      'vue/multi-word-component-names': 'off',
    },
  },
  {
    files: ['**/__tests__/**/*.test.js'],
    languageOptions: {
      globals: {
        ...globals.node,
        vi: 'readonly',
        describe: 'readonly',
        it: 'readonly',
        expect: 'readonly',
        beforeEach: 'readonly',
        afterEach: 'readonly',
      },
    },
  },
]
