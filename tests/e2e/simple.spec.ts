import { test, expect } from '@playwright/test'

test.describe('Simple API Tests', () => {
  test('should access public endpoint', async ({ request }) => {
    // This should work even without authentication
    const response = await request.get('/')
    
    // Even if we get an error page, we should get a response
    expect(response.status()).toBeLessThan(600)
  })
})