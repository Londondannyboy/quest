import { defineConfig } from 'checkly'

/**
 * Checkly configuration for Quest Core V2
 * See: https://www.checklyhq.com/docs/cli/configuration-reference/
 */
export default defineConfig({
  projectName: 'Quest Core V2',
  logicalId: 'quest-core-v2',
  repoUrl: 'https://github.com/Londondannyboy/quest.git',
  checks: {
    activated: true,
    muted: false,
    runtimeId: '2024.02',
    frequency: 10,
    locations: ['us-east-1', 'eu-west-1'],
    tags: ['production', 'api', 'browser'],
    checkMatch: '**/__checks__/**/*.check.ts',
    browserChecks: {
      testMatch: '**/__checks__/**/*.spec.ts',
    },
  },
  cli: {
    runLocation: 'us-east-1',
    privateRunLocation: 'private-dc1',
  },
})