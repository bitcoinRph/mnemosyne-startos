import assert from 'node:assert/strict'
import {
  parseTokenStoreJson,
  tokenStoreShape,
} from '../startos/fileModels/tokenStoreShape.ts'

const accepted = tokenStoreShape.parse({
  tokens: { Alice: 'secret-1', bob: 'secret-2' },
})
assert.deepEqual(accepted.tokens, { Alice: 'secret-1', bob: 'secret-2' })

const caseDistinct = tokenStoreShape.parse({
  tokens: { Alice: 'secret-1', alice: 'secret-2' },
})
assert.deepEqual(caseDistinct.tokens, { Alice: 'secret-1', alice: 'secret-2' })

const padded = tokenStoreShape.parse(
  parseTokenStoreJson('{"tokens":{" Alice ":" secret-1 ","bob":" secret-2"}}'),
)
assert.deepEqual(padded.tokens, { Alice: 'secret-1', bob: 'secret-2' })

assert.throws(
  () => parseTokenStoreJson('{"tokens":{"alice":"one","alice":"two"}}'),
  /duplicate/i,
)

assert.throws(() => parseTokenStoreJson('{'), /Invalid token store JSON/)
assert.equal(
  tokenStoreShape.safeParse(parseTokenStoreJson('{}')).success,
  false,
)

const malformedStates = [
  {},
  { tokens: null },
  { tokens: [] },
  { tokens: { '': 'secret' } },
  { tokens: { '   ': 'secret' } },
  { tokens: { alice: '' } },
  { tokens: { alice: '   ' } },
  { tokens: { alice: 'same', bob: 'same' } },
  { tokens: { alice: ' same ', bob: 'same' } },
  { tokens: { alice: 'one', ' alice ': 'two' } },
] as const

for (const malformed of malformedStates) {
  assert.equal(
    tokenStoreShape.safeParse(malformed).success,
    false,
    JSON.stringify(malformed),
  )
}

console.log('token store contract tests passed')
