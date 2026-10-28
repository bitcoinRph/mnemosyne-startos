import { z } from '@start9labs/start-sdk'

export type TokenStore = {
  tokens: Record<string, string>
  [key: string]: unknown
}

/** A strict JSON parser that rejects duplicate members before object collapse. */
class DuplicateAwareJsonParser {
  private offset = 0
  private readonly input: string

  constructor(input: string) {
    this.input = input
  }

  parse(): unknown {
    const value = this.parseValue()
    this.skipWhitespace()
    if (this.offset !== this.input.length)
      this.fail('unexpected trailing input')
    return value
  }

  private parseValue(): unknown {
    this.skipWhitespace()
    const current = this.input[this.offset]
    if (current === '{') return this.parseObject()
    if (current === '[') return this.parseArray()
    if (current === '"') return this.parseString()
    if (current === 't') return this.parseLiteral('true', true)
    if (current === 'f') return this.parseLiteral('false', false)
    if (current === 'n') return this.parseLiteral('null', null)
    if (current === '-' || this.isDigit(current)) return this.parseNumber()
    this.fail('expected a JSON value')
  }

  private parseObject(): Record<string, unknown> {
    this.offset += 1
    const value: Record<string, unknown> = {}
    const names = new Set<string>()
    this.skipWhitespace()
    if (this.input[this.offset] === '}') {
      this.offset += 1
      return value
    }

    while (true) {
      this.skipWhitespace()
      if (this.input[this.offset] !== '"')
        this.fail('expected an object member name')
      const name = this.parseString()
      if (names.has(name))
        this.fail(`duplicate JSON object member ${JSON.stringify(name)}`)
      names.add(name)
      this.skipWhitespace()
      if (this.input[this.offset] !== ':')
        this.fail('expected a colon after object member')
      this.offset += 1
      Object.defineProperty(value, name, {
        configurable: true,
        enumerable: true,
        value: this.parseValue(),
        writable: true,
      })
      this.skipWhitespace()
      const delimiter = this.input[this.offset]
      if (delimiter === '}') {
        this.offset += 1
        return value
      }
      if (delimiter !== ',') this.fail('expected a comma or closing brace')
      this.offset += 1
    }
  }

  private parseArray(): unknown[] {
    this.offset += 1
    const value: unknown[] = []
    this.skipWhitespace()
    if (this.input[this.offset] === ']') {
      this.offset += 1
      return value
    }

    while (true) {
      value.push(this.parseValue())
      this.skipWhitespace()
      const delimiter = this.input[this.offset]
      if (delimiter === ']') {
        this.offset += 1
        return value
      }
      if (delimiter !== ',') this.fail('expected a comma or closing bracket')
      this.offset += 1
    }
  }

  private parseString(): string {
    const start = this.offset
    this.offset += 1
    while (this.offset < this.input.length) {
      const current = this.input[this.offset]
      if (current === '"') {
        this.offset += 1
        return JSON.parse(this.input.slice(start, this.offset)) as string
      }
      if (current === '\\') {
        this.offset += 2
      } else {
        if (current.charCodeAt(0) < 0x20)
          this.fail('unescaped control character')
        this.offset += 1
      }
    }
    this.fail('unterminated string')
  }

  private parseNumber(): number {
    const start = this.offset
    if (this.input[this.offset] === '-') this.offset += 1
    if (this.input[this.offset] === '0') {
      this.offset += 1
    } else {
      this.consumeDigits(true)
    }
    if (this.input[this.offset] === '.') {
      this.offset += 1
      this.consumeDigits(true)
    }
    if (this.input[this.offset] === 'e' || this.input[this.offset] === 'E') {
      this.offset += 1
      if (this.input[this.offset] === '+' || this.input[this.offset] === '-') {
        this.offset += 1
      }
      this.consumeDigits(true)
    }
    return JSON.parse(this.input.slice(start, this.offset)) as number
  }

  private consumeDigits(required: boolean): void {
    const start = this.offset
    while (this.isDigit(this.input[this.offset])) this.offset += 1
    if (required && start === this.offset) this.fail('expected a digit')
  }

  private isDigit(value: string | undefined): boolean {
    return value !== undefined && value >= '0' && value <= '9'
  }

  private parseLiteral<T>(text: string, value: T): T {
    if (this.input.slice(this.offset, this.offset + text.length) !== text) {
      this.fail(`expected ${text}`)
    }
    this.offset += text.length
    return value
  }

  private skipWhitespace(): void {
    while (
      this.input[this.offset] === ' ' ||
      this.input[this.offset] === '\n' ||
      this.input[this.offset] === '\r' ||
      this.input[this.offset] === '\t'
    ) {
      this.offset += 1
    }
  }

  private fail(message: string): never {
    throw new SyntaxError(
      `Invalid token store JSON at offset ${this.offset}: ${message}`,
    )
  }
}

export const parseTokenStoreJson = (raw: string): unknown =>
  new DuplicateAwareJsonParser(raw).parse()

export const tokenStoreShape = z
  .looseObject({
    tokens: z.record(z.string(), z.string()),
  })
  .superRefine(({ tokens }, context) => {
    const names = new Set<string>()
    const secrets = new Set<string>()

    for (const [name, secret] of Object.entries(tokens)) {
      const cleanName = name.trim()
      const cleanSecret = secret.trim()

      if (!cleanName) {
        context.addIssue({
          code: 'custom',
          message: 'Agent names must be non-empty after trimming',
          path: ['tokens', name],
        })
      } else if (names.has(cleanName)) {
        context.addIssue({
          code: 'custom',
          message: 'Agent names must be unique after trimming',
          path: ['tokens', name],
        })
      }
      names.add(cleanName)

      if (!cleanSecret) {
        context.addIssue({
          code: 'custom',
          message: 'Agent secrets must be non-empty after trimming',
          path: ['tokens', name],
        })
      } else if (secrets.has(cleanSecret)) {
        context.addIssue({
          code: 'custom',
          message: 'Agent secrets must be unique after trimming',
          path: ['tokens', name],
        })
      }
      secrets.add(cleanSecret)
    }
  })
  .transform(({ tokens, ...rest }) => ({
    ...rest,
    tokens: Object.fromEntries(
      Object.entries(tokens).map(([name, secret]) => [
        name.trim(),
        secret.trim(),
      ]),
    ),
  }))
