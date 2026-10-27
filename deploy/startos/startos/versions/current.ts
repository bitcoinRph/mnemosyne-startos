import { IMPOSSIBLE, VersionInfo } from '@start9labs/start-sdk'

export const current = VersionInfo.of({
  version: '4.0.0-beta.6:0',
  releaseNotes: {
    en_US:
      'Initial StartOS release: Mnemosyne 4.0.0b6 with MCP and REST API on one port, per-agent tokens, and an offline embedding model.',
    es_ES:
      'Versión inicial para StartOS: Mnemosyne 4.0.0b6 con MCP y API REST en un mismo puerto, tokens por agente y un modelo de embeddings sin conexión.',
    de_DE:
      'Erste StartOS-Veröffentlichung: Mnemosyne 4.0.0b6 mit MCP und REST-API auf einem Port, Tokens pro Agent und einem Offline-Embedding-Modell.',
    pl_PL:
      'Pierwsze wydanie dla StartOS: Mnemosyne 4.0.0b6 z MCP i API REST na jednym porcie, tokenami dla każdego agenta i modelem embeddingów działającym offline.',
    fr_FR:
      'Version initiale pour StartOS : Mnemosyne 4.0.0b6 avec MCP et API REST sur un seul port, un jeton par agent et un modèle d’embeddings hors ligne.',
  },
  migrations: {
    up: async ({ effects }) => {},
    down: IMPOSSIBLE,
  },
})
