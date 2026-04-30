import '@testing-library/jest-dom'
import { afterEach, beforeEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => {
  cleanup()
})

beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation((...args: unknown[]) => {
    const message = typeof args[0] === 'string' ? args[0] : ''
    if (message.includes('not wrapped in act(')) {
      throw new Error(`Memory leak / async update after unmount detected: ${message}`)
    }
  })
})

afterEach(() => {
  vi.restoreAllMocks()
})
