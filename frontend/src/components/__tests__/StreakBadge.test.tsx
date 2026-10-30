import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

// Mock dependencies before importing component
vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { uid: 'test-uid' } }),
}))
vi.mock('@/services/firestore-plan', () => ({
  getStreak: vi.fn().mockResolvedValue({ current: 5, longest: 10 }),
}))

import StreakBadge from '../StreakBadge'

describe('StreakBadge', () => {
  it('renders compact badge', async () => {
    render(<StreakBadge compact />)
    // Should render the flame icon and number after data loads
    await waitFor(() => {
      expect(screen.getByText('5')).toBeInTheDocument()
    })
  })

  it('renders full card', async () => {
    render(<StreakBadge />)
    expect(screen.getByText(/günlük seri/)).toBeInTheDocument()
  })
})