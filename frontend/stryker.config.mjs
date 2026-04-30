/** @type {import('@stryker-mutator/api/core').PartialStrykerOptions} */
export default {
  testRunner: 'vitest',
  vitest: {
    configFile: 'vite.config.ts',
  },
  mutate: [
    'src/**/*.ts',
    'src/**/*.tsx',
    '!src/**/*.test.ts',
    '!src/**/*.test.tsx',
    '!src/test/**/*',
    '!src/main.tsx',
  ],
  thresholds: {
    high: 80,
    low: 70,
    break: 70,
  },
  coverageAnalysis: 'perTest',
  reporters: ['progress', 'clear-text'],
  tempDirName: '.stryker-tmp',
  cleanTempDir: true,
}
