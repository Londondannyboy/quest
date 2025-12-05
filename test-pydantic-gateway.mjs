/**
 * Test Pydantic AI Gateway
 *
 * Tests multiple providers through the gateway to validate routing works.
 *
 * Usage: node test-pydantic-gateway.mjs
 */

import { config } from 'dotenv';
config();

const API_KEY = process.env.PYDANTIC_AI_GATEWAY_API_KEY;

if (!API_KEY) {
  console.error('❌ PYDANTIC_AI_GATEWAY_API_KEY not set');
  console.log('   Set it in .env or export it');
  process.exit(1);
}

console.log('🔑 API Key found:', API_KEY.slice(0, 10) + '...');

/**
 * Test OpenAI via Pydantic Gateway
 */
async function testOpenAI() {
  console.log('\n📡 Testing OpenAI (gpt-4o-mini) via Gateway...');

  const response = await fetch('https://gateway.pydantic.dev/proxy/openai/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: 'You are a helpful assistant. Be brief.' },
        { role: 'user', content: 'What is 2+2? Just the number.' },
      ],
      max_tokens: 50,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    console.error('❌ OpenAI Error:', response.status, error);
    return false;
  }

  const data = await response.json();
  const content = data.choices?.[0]?.message?.content;
  console.log('✅ OpenAI Response:', content);
  return true;
}

/**
 * Test Groq via Pydantic Gateway (cheaper!)
 */
async function testGroq() {
  console.log('\n📡 Testing Groq (llama-3.1-8b-instant) via Gateway...');

  const response = await fetch('https://gateway.pydantic.dev/proxy/groq/openai/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'llama-3.1-8b-instant',
      messages: [
        { role: 'system', content: 'You are a helpful assistant. Be brief.' },
        { role: 'user', content: 'What is 3+3? Just the number.' },
      ],
      max_tokens: 50,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    console.error('❌ Groq Error:', response.status, error);
    return false;
  }

  const data = await response.json();
  const content = data.choices?.[0]?.message?.content;
  console.log('✅ Groq Response:', content);
  return true;
}

/**
 * Test Anthropic via Pydantic Gateway
 */
async function testAnthropic() {
  console.log('\n📡 Testing Anthropic (claude-3-5-haiku) via Gateway...');

  const response = await fetch('https://gateway.pydantic.dev/proxy/anthropic/v1/messages', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json',
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model: 'claude-3-5-haiku-latest',
      max_tokens: 50,
      messages: [
        { role: 'user', content: 'What is 4+4? Just the number.' },
      ],
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    console.error('❌ Anthropic Error:', response.status, error);
    return false;
  }

  const data = await response.json();
  const content = data.content?.[0]?.text;
  console.log('✅ Anthropic Response:', content);
  return true;
}

/**
 * Test the unified /proxy/chat/ endpoint (used by Python)
 */
async function testUnifiedChat() {
  console.log('\n📡 Testing Unified Chat endpoint (gpt-4o-mini)...');

  const response = await fetch('https://gateway.pydantic.dev/proxy/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'user', content: 'What is 5+5? Just the number.' },
      ],
      max_tokens: 50,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    console.error('❌ Unified Chat Error:', response.status, error);
    return false;
  }

  const data = await response.json();
  const content = data.choices?.[0]?.message?.content;
  console.log('✅ Unified Chat Response:', content);
  return true;
}

// Run all tests
async function main() {
  console.log('🚀 Pydantic AI Gateway Test Suite\n');
  console.log('='.repeat(50));

  const results = {
    openai: await testOpenAI(),
    groq: await testGroq(),
    anthropic: await testAnthropic(),
    unified: await testUnifiedChat(),
  };

  console.log('\n' + '='.repeat(50));
  console.log('\n📊 Results Summary:');
  Object.entries(results).forEach(([provider, success]) => {
    console.log(`   ${success ? '✅' : '❌'} ${provider}`);
  });

  const allPassed = Object.values(results).every(Boolean);
  console.log(`\n${allPassed ? '🎉 All tests passed!' : '⚠️  Some tests failed'}`);
}

main().catch(console.error);
