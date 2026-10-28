import assert from 'node:assert/strict'
import { tokenStoreShape } from '../startos/fileModels/tokenStoreShape.ts'

const accepted = tokenStoreShape.parse({
  tokens: { Alice: 'secret-1', bob: 'secret-2' },
})
assert.deepEqual(accepted.tokens, { Alice: 'secret-1', bob: 'secret-2' })

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
  { tokens: { Alice: 'one', alice: 'two' } },
] as const

for (const malformed of malformedStates) {
  assert.equal(
    tokenStoreShape.safeParse(malformed).success,
    false,
    JSON.stringify(malformed),
  )
}

console.log(`${malformedStates.length + 1} store schema contract cases passed`)
