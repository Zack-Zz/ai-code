import test from 'node:test';
import assert from 'node:assert/strict';
import { createTranslator, normalizeLocale, loadLocale, saveLocale, LOCALE_KEY } from '../src/i18n-core.js';

test('language preference normalizes supported languages and keeps Chinese as the existing default', () => {
  assert.equal(normalizeLocale('en-US'), 'en');
  assert.equal(normalizeLocale('en'), 'en');
  assert.equal(normalizeLocale('zh-CN'), 'zh-CN');
  assert.equal(normalizeLocale('fr'), 'zh-CN');
});
test('stored locale survives reload and storage failures preserve an in-memory usable preference', () => {
  const data = new Map();
  const storage = { getItem: key => data.get(key), setItem: (key,value) => data.set(key,value) };
  assert.equal(loadLocale(storage), 'zh-CN');
  assert.equal(saveLocale(storage, 'en'), true);
  assert.equal(data.get(LOCALE_KEY), 'en');
  assert.equal(loadLocale(storage), 'en');
  assert.equal(loadLocale({getItem(){ throw Error('blocked'); }}), 'zh-CN');
  assert.equal(saveLocale({setItem(){ throw Error('full'); }}, 'en'), false);
});
test('fixed interface messages switch languages while unknown business content is preserved', () => {
  const en = createTranslator('en'), zh = createTranslator('zh-CN');
  assert.equal(en('我的看板'), 'My board');
  assert.equal(zh('我的看板'), '我的看板');
  assert.equal(en('成员导入失败后自动补偿'), '成员导入失败后自动补偿');
  assert.equal(en('feature/需求-R&{id}'), 'feature/需求-R&{id}');
});
test('complete message templates interpolate raw data without recursively translating it', () => {
  const en = createTranslator('en'), zh = createTranslator('zh-CN');
  assert.equal(en('共 {count} 个任务', { count: 3 }), 'Tasks · 3');
  assert.equal(zh('共 {count} 个任务', { count: 3 }), '共 3 个任务');
  assert.equal(en('任务详情 · {title}', { title: '我的看板 $& {count}' }), 'Task details · 我的看板 $& {count}');
});
test('existing model feedback uses centrally registered full templates, never substring replacement', () => {
  const en = createTranslator('en');
  assert.equal(en('请先完成「需求」阶段验收'), 'Accept the Requirements stage first');
  assert.equal(en('备注：请先完成「需求」阶段验收'), '备注：请先完成「需求」阶段验收');
});
test('combined workflow gate feedback translates registered items without guessing unknown text', () => {
  const en = createTranslator('en');
  const first = '任务已暂停，请先恢复任务', second = '前序阶段尚未验收通过';
  assert.equal(en(`${first}；${second}`), `${en(first)} · ${en(second)}`);
  assert.equal(en(`${first}；用户自己的备注`), `${first}；用户自己的备注`);
});
