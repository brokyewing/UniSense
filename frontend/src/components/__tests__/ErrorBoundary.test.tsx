import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import ErrorBoundary from '../ErrorBoundary'

describe('ErrorBoundary', () => {
  it('renders children when no error', () => {
    render(
      <ErrorBoundary>
        <div>Çocuk içerik</div>
      </ErrorBoundary>
    )
    expect(screen.getByText('Çocuk içerik')).toBeInTheDocument()
  })

  it('shows error UI when child throws', () => {
    const Thrower = () => { throw new Error('boom') }
    // Suppress console.error noise
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <ErrorBoundary>
        <Thrower />
      </ErrorBoundary>
    )
    expect(screen.getByText('Bir şeyler ters gitti')).toBeInTheDocument()
    spy.mockRestore()
  })
})