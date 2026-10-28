import { setupManifest } from '@start9labs/start-sdk'
import { long, short } from './i18n'

export const manifest = setupManifest({
  id: 'mnemosyne',
  title: 'Mnemosyne',
  license: 'MIT',
  packageRepo: 'https://github.com/bitcoinRph/mnemosyne-startos',
  upstreamRepo: 'https://github.com/mnemosyne-oss/mnemosyne',
  marketingUrl: 'https://github.com/mnemosyne-oss/mnemosyne',
  donationUrl: null,
  description: { short, long },
  volumes: ['main', 'startos'],
  images: {
    mnemosyne: {
      source: {
        dockerBuild: {
          workdir: '../..',
          dockerfile: './Dockerfile',
        },
      },
      arch: ['x86_64', 'aarch64'],
    },
  },
})
