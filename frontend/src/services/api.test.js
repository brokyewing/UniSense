import { describe, it, expect } from 'vitest'
import { ApiError, API_BASE } from './api'

describe('api', () => {
  it('should export ApiError class', () => {
    const err = new ApiError('test', 404)
    expect(err).toBeInstanceOf(Error)
    expect(err.message).toBe('test')
    expect(err.status).toBe(404)
    expect(err.name).toBe('ApiError')
  })

  it('should export API_BASE', () => {
    expect(typeof API_BASE).toBe('string')
  })
})