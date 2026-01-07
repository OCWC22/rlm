#!/usr/bin/env node
/**
 * Test all: LFM2.5 + Qwen 3 2B
 */

const { execSync } = require('child_process');
const path = require('path');

console.log('🧪 Running All Tests\n');
console.log('='.repeat(50));

try {
  console.log('\n1️⃣ Testing LFM2.5...\n');
  execSync('node test/test-lfm2.5.js', {
    cwd: path.join(__dirname, '..'),
    stdio: 'inherit',
  });
  
  console.log('\n' + '='.repeat(50));
  console.log('\n2️⃣ Testing Qwen 3...\n');
  execSync('node test/test-qwen.js', {
    cwd: path.join(__dirname, '..'),
    stdio: 'inherit',
  });
  
  console.log('\n' + '='.repeat(50));
  console.log('\n✅ All tests complete!\n');
} catch (error) {
  console.error('\n❌ Test failed:', error.message);
  process.exit(1);
}

