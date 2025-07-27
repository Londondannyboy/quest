import { headers } from 'next/headers'
import { WebhookEvent } from '@clerk/nextjs/server'
import { Webhook } from 'svix'
import { prisma } from '@/lib/prisma'

export const dynamic = 'force-dynamic'

export async function POST(req: Request) {
  // For now, just log the webhook to verify it's working
  console.log('Clerk webhook received')
  
  const WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET

  if (!WEBHOOK_SECRET) {
    console.log('CLERK_WEBHOOK_SECRET not set')
    return new Response('Webhook secret not configured', { status: 500 })
  }

  // Get the headers
  const headerPayload = await headers()
  const svix_id = headerPayload.get("svix-id")
  const svix_timestamp = headerPayload.get("svix-timestamp")
  const svix_signature = headerPayload.get("svix-signature")

  // If there are no headers, error out
  if (!svix_id || !svix_timestamp || !svix_signature) {
    return new Response('Error occured -- no svix headers', {
      status: 400
    })
  }

  // Get the body
  const payload = await req.json()
  const body = JSON.stringify(payload)

  // Create a new Svix instance with your secret
  const wh = new Webhook(WEBHOOK_SECRET)

  let evt: WebhookEvent

  // Verify the payload with the headers
  try {
    evt = wh.verify(body, {
      "svix-id": svix_id,
      "svix-timestamp": svix_timestamp,
      "svix-signature": svix_signature,
    }) as WebhookEvent
  } catch (err) {
    console.error('Error verifying webhook:', err)
    return new Response('Error occured', {
      status: 400
    })
  }

  // Handle the webhook
  const eventType = evt.type
  console.log(`Webhook type: ${eventType}`)
  console.log('User data:', evt.data)

  if (eventType === 'user.created') {
    const { id, email_addresses } = evt.data
    
    try {
      const user = await prisma.user.create({
        data: {
          clerkId: id,
          email: email_addresses[0].email_address,
        }
      })
      console.log('User created in database:', user.id)
    } catch (error) {
      console.error('Error creating user in database:', error)
      // Don't fail the webhook if database fails
    }
  }

  if (eventType === 'user.updated') {
    const { id, email_addresses } = evt.data
    
    try {
      const user = await prisma.user.update({
        where: { clerkId: id },
        data: {
          email: email_addresses[0].email_address,
        }
      })
      console.log('User updated in database:', user.id)
    } catch (error) {
      console.error('Error updating user in database:', error)
    }
  }

  return new Response('Webhook received', { status: 200 })
}