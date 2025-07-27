#!/usr/bin/env node

/**
 * Debug script for Vercel deployment environment variables
 * Run this locally and compare with what's in Vercel
 */

const fs = require('fs');
const path = require('path');

console.log('=== Vercel Environment Variable Debug ===\n');

// Check for environment files
const envFiles = ['.env', '.env.local', '.env.production', '.env.development'];
console.log('Checking for environment files:');
envFiles.forEach(file => {
  const exists = fs.existsSync(path.join(process.cwd(), file));
  console.log(`  ${file}: ${exists ? '✓ Found' : '✗ Not found'}`);
});

console.log('\n=== Required Environment Variables ===\n');

// Define required variables based on your schema
const requiredVars = {
  // Database - Neon
  'DATABASE_URL': 'PostgreSQL connection string (with pooling)',
  'DIRECT_URL': 'PostgreSQL direct connection string (without pooling)',
  
  // Clerk Authentication
  'NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY': 'Clerk publishable key (starts with pk_)',
  'CLERK_SECRET_KEY': 'Clerk secret key (starts with sk_)',
  'CLERK_WEBHOOK_SECRET': 'Clerk webhook secret (starts with whsec_)',
  
  // Optional but recommended
  'NODE_ENV': 'Environment (production/development)',
};

// Check each variable
Object.entries(requiredVars).forEach(([key, description]) => {
  const value = process.env[key];
  const isSet = !!value;
  
  console.log(`${key}:`);
  console.log(`  Description: ${description}`);
  console.log(`  Status: ${isSet ? '✓ Set' : '✗ Not set'}`);
  
  if (isSet && key.includes('DATABASE')) {
    // Parse database URL to check format
    try {
      const url = new URL(value);
      console.log(`  Host: ${url.hostname}`);
      console.log(`  Database: ${url.pathname.slice(1)}`);
      console.log(`  SSL: ${url.searchParams.has('sslmode')}`);
    } catch (e) {
      console.log('  ⚠️  Invalid URL format');
    }
  }
  
  console.log('');
});

console.log('=== Neon Database URL Format ===\n');
console.log('Expected format for DATABASE_URL:');
console.log('  postgresql://[user]:[password]@[neon-hostname]/[database]?sslmode=require');
console.log('\nExpected format for DIRECT_URL:');
console.log('  postgresql://[user]:[password]@[neon-hostname]/[database]?sslmode=require');
console.log('\nNote: Both URLs might be the same for Neon, or DATABASE_URL might use pooling');

console.log('\n=== Vercel Configuration Checklist ===\n');
console.log('1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables');
console.log('2. Ensure ALL required variables are set for Production environment');
console.log('3. Variable names must match EXACTLY (case-sensitive)');
console.log('4. If using Neon integration, check if variables are prefixed (e.g., NEON_DATABASE_URL)');
console.log('5. After adding/updating variables, you MUST redeploy');
console.log('\n=== Common Issues ===\n');
console.log('- If you see "neon_database" in Vercel, that might be a prefix');
console.log('- Check for NEON_DATABASE_URL or POSTGRES_URL as alternatives');
console.log('- Middleware fails if Prisma tries to connect before env vars are loaded');
console.log('- Edge runtime (middleware) has different env var access than Node runtime');