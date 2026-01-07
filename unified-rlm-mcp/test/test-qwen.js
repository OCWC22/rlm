#!/usr/bin/env node
/**
 * Test Qwen 3 2B via MCP
 * Requires: Ollama running with Qwen 3 models
 */

const { spawn } = require('child_process');
const path = require('path');

const SERVER_PATH = path.join(__dirname, '../dist/index.js');

console.log('🧪 Testing Qwen 3 2B via Unified RLM MCP\n');
console.log('Prerequisites:');
console.log('  1. Ollama running: ollama serve');
console.log('  2. Qwen 3 models pulled:');
console.log('     ollama pull qwen3:0.6b');
console.log('     ollama pull qwen3:1.7b');
console.log('     ollama pull qwen3:4b');
console.log('     ollama pull qwen3:8b\n');

const server = spawn('node', [SERVER_PATH], {
  env: {
    ...process.env,
    RLM_PROVIDER: 'ollama',
    RLM_MODEL_LOCAL: 'ollama/qwen3:1.7b',
    RLM_DEBUG: 'true',
  },
  stdio: ['pipe', 'pipe', 'inherit'],
});

let requestId = 1;

function sendRequest(method, params = {}) {
  const id = requestId++;
  const req = {
    jsonrpc: '2.0',
    id,
    method,
    params,
  };
  server.stdin.write(JSON.stringify(req) + '\n');
  return id;
}

function sendToolCall(toolName, args) {
  return sendRequest('tools/call', {
    name: toolName,
    arguments: args,
  });
}

let output = '';
server.stdout.on('data', (data) => {
  output += data.toString();
});

// Initialize
sendRequest('initialize', {
  protocolVersion: '2024-11-05',
  capabilities: {},
  clientInfo: { name: 'test-qwen', version: '1.0.0' },
});

setTimeout(() => {
  console.log('📋 Step 1: List Qwen models\n');
  sendToolCall('rlm', { mode: 'models' });
}, 500);

setTimeout(() => {
  console.log('\n📥 Step 2: Ingest test data\n');
  sendToolCall('rlm', {
    mode: 'ingest',
    sessionId: 'test-qwen',
    data: 'Qwen 3 is a family of open-source language models by Alibaba. It includes models from 0.6B to 235B parameters. Qwen 3 features hybrid thinking/non-thinking modes and excellent multilingual capabilities.',
    name: 'qwen-info',
  });
}, 1500);

setTimeout(() => {
  console.log('\n🤔 Step 3: Process with Qwen 3 1.7B (closest to 2B)\n');
  sendToolCall('rlm', {
    mode: 'process',
    sessionId: 'test-qwen',
    prompt: 'What are the key features of Qwen 3? List 5 main points.',
    model: 'ollama/qwen3:1.7b',
    systemPrompt: 'You are a helpful assistant. Provide clear, structured answers.',
  });
}, 2500);

setTimeout(() => {
  console.log('\n🔍 Step 4: Search ingested data\n');
  sendToolCall('rlm', {
    mode: 'search',
    sessionId: 'test-qwen',
    query: 'Qwen',
    maxResults: 5,
  });
}, 3500);

setTimeout(() => {
  console.log('\n💭 Step 5: Chain-of-thought reasoning\n');
  sendToolCall('rlm', {
    mode: 'think',
    sessionId: 'test-qwen',
    pattern: 'chain',
    input: 'Why would someone choose Qwen 3 1.7B over larger models?',
    model: 'ollama/qwen3:1.7b',
    steps: 3,
  });
}, 4500);

setTimeout(() => {
  console.log('\n💰 Step 6: Check budget\n');
  sendToolCall('state', {
    op: 'budget',
    sessionId: 'test-qwen',
  });
}, 5500);

setTimeout(() => {
  server.kill();
  
  console.log('\n\n=== RESULTS ===\n');
  
  // Parse responses
  const lines = output.split('\n').filter(Boolean);
  let step = 0;
  
  for (const line of lines) {
    try {
      const json = JSON.parse(line);
      
      if (json.result?.content?.[0]?.text) {
        const content = json.result.content[0].text;
        
        try {
          const data = JSON.parse(content);
          
          step++;
          
          if (data.models) {
            console.log(`✅ Step ${step}: Models listed`);
            const qwenModels = data.models.filter(m => m.name.includes('qwen3'));
            console.log(`   Found ${qwenModels.length} Qwen 3 models:`);
            qwenModels.slice(0, 5).forEach(m => {
              console.log(`   - ${m.name} (${m.params || 'N/A'})`);
            });
          } else if (data.path) {
            console.log(`✅ Step ${step}: Data ingested at ${data.path}`);
          } else if (data.response) {
            console.log(`✅ Step ${step}: LLM Response`);
            console.log(`   ${data.response.substring(0, 300)}...`);
            console.log(`   Tokens: ${data.tokensUsed}, Model: ${data.model}`);
          } else if (data.matches) {
            console.log(`✅ Step ${step}: Search found ${data.matches.length} matches`);
            data.matches.slice(0, 3).forEach(m => {
              console.log(`   Line ${m.line}: ${m.content.substring(0, 80)}...`);
            });
          } else if (data.thoughts) {
            console.log(`✅ Step ${step}: Reasoning chain (${data.thoughts.length} steps)`);
            console.log(`   Final conclusion: ${data.conclusion.substring(0, 200)}...`);
          } else if (data.budget) {
            console.log(`✅ Step ${step}: Budget status`);
            console.log(`   Used: ${data.used.tokens} tokens, $${data.used.cost}`);
            console.log(`   OK: ${data.ok}`);
          }
        } catch {
          if (content.length < 300) {
            console.log(`Response: ${content}`);
          }
        }
      }
    } catch {
      // Skip non-JSON
    }
  }
  
  console.log('\n✅ Qwen 3 test complete!\n');
}, 6500);

