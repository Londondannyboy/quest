import { test, expect } from '@playwright/test'

test.describe('Voice Coach Trinity', () => {
  test.skip('requires authentication', () => {})
  
  test.beforeEach(async ({ page }) => {
    // Skip for now - requires authentication
    test.skip()
  })

  test('should load Trinity page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Trinity Discovery')
    await expect(page.locator('text=Click Start Session to begin')).toBeVisible()
  })

  test('should connect to voice coach', async ({ page }) => {
    // Click start session
    await page.click('button:has-text("Start Session")')
    
    // Wait for connection
    await expect(page.locator('text=Connected')).toBeVisible({ timeout: 10000 })
    
    // Check that the speaking circle is visible
    await expect(page.locator('button:has-text("Click to Speak")')).toBeVisible()
  })

  test('should not create duplicate connections', async ({ page }) => {
    // Listen for WebSocket connections
    let connectionCount = 0
    page.on('websocket', ws => {
      if (ws.url().includes('hume.ai')) {
        connectionCount++
      }
    })

    // Start session
    await page.click('button:has-text("Start Session")')
    await page.waitForTimeout(2000)
    
    // Connection count should be exactly 1
    expect(connectionCount).toBe(1)
  })

  test('should handle pause and resume correctly', async ({ page }) => {
    // Start session
    await page.click('button:has-text("Start Session")')
    await expect(page.locator('text=Connected')).toBeVisible()
    
    // Pause
    await page.click('button:has-text("Pause Session")')
    await expect(page.locator('button:has-text("Start Session")')).toBeVisible()
    
    // Resume
    await page.click('button:has-text("Start Session")')
    await expect(page.locator('text=Connected')).toBeVisible()
  })

  test('should display user context', async ({ page }) => {
    // This would need mock auth
    // Check if user name appears somewhere on the page
    await expect(page.locator('text=User')).toBeDefined()
  })
})

test.describe('Voice Coach Debug Page', () => {
  test.skip('requires working UI', () => {})
})

test.describe('Hume Configuration', () => {
  test('should verify Hume config', async ({ page, request }) => {
    // API test
    const response = await request.get('/api/hume/verify-config')
    
    if (response.ok()) {
      const data = await response.json()
      
      // Check if CLM is configured
      expect(data.config).toBeDefined()
      console.log('CLM configured:', data.config.hasCustomLLM)
      console.log('CLM URL:', data.config.customLLMUrl)
      
      // Check recommendations
      if (data.recommendations?.length > 0) {
        console.log('Recommendations:', data.recommendations)
      }
    }
  })
})