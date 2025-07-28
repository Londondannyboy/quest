import { BrowserCheck } from 'checkly/constructs'
import { expect, test } from '@playwright/test'

new BrowserCheck('homepage-check', {
  name: 'Homepage Browser Check',
  frequency: 10,
  locations: ['us-east-1', 'eu-west-1'],
})

test('Homepage loads correctly', async ({ page }) => {
  // Use Vercel preview URL if available, otherwise production
  const targetUrl = process.env.ENVIRONMENT_URL || 'https://quest-omega-wheat.vercel.app'
  
  const response = await page.goto(targetUrl)
  
  // Check response
  expect(response?.status(), 'should respond with correct status code').toBeLessThan(400)
  
  // Check page title
  await expect(page).toHaveTitle(/Quest Core V2/)
  
  // Check main heading is visible
  await expect(page.locator('h1')).toContainText('Quest Core V2')
  
  // Check sign in button is visible  
  await expect(page.getByText('Sign In')).toBeVisible()
  
  // Take a screenshot for visual validation
  await page.screenshot({ path: 'homepage.jpg' })
})