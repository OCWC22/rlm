#!/usr/bin/env node
/**
 * Test LFM2.5 via MCP
 * Requires: Ollama running with LFM2.5 models
 */

const { spawn } = require('child_process');
const path = require('path');

const SERVER_PATH = path.join(__dirname, '../dist/index.js');

console.log('🧪 Testing LFM2.5 via Unified RLM MCP\n');
console.log('Prerequisites:');
console.log('  1. Ollama running: ollama serve');
console.log('  2. LFM2.5 models pulled:');
console.log('     ollama pull lfm2.5:1.2b');
console.log('     ollama pull lfm2.5-audio');
console.log('     ollama pull lfm2.5-vl:1.6b\n');

const server = spawn('node', [SERVER_PATH], {
  env: {
    ...process.env,
    RLM_PROVIDER: 'ollama',
    RLM_MODEL_LOCAL: 'ollama/lfm2.5:1.2b',
    RLM_DEBUG: 'true',
  },
  stdio: ['pipe', 'pipe', 'inherit'],
});

let requestId = 1;
const requests = [];

function sendRequest(method, params = {}) {
  const id = requestId++;
  const req = {
    jsonrpc: '2.0',
    id,
    method,
    params,
  };
  server.stdin.write(JSON.stringify(req) + '\n');
  requests.push({ id, method, params });
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
  clientInfo: { name: 'test-lfm2.5', version: '1.0.0' },
});

setTimeout(() => {
  console.log('📋 Step 1: List available models\n');
  sendToolCall('rlm', { mode: 'models' });
}, 500);

setTimeout(() => {
  console.log('\n📥 Step 2: Ingest test data\n');
  sendToolCall('rlm', {
    mode: 'ingest',
    sessionId: 'test-lfm2.5',
    data: {
      task: 'Test LFM2.5 capabilities',
      timestamp: new Date().toISOString(),
      models: ['lfm2.5:1.2b', 'lfm2.5-audio', 'lfm2.5-vl:1.6b'],
    },
    name: 'test-data',
  });
}, 1500);

setTimeout(() => {
  console.log('\n🤔 Step 3: Process with LFM2.5-1.2B\n');
  sendToolCall('rlm', {
    mode: 'process',
    sessionId: 'test-lfm2.5',
    prompt: 'What are the key features of LFM2.5? Summarize in 3 bullet points.',
    model: 'ollama/lfm2.5:1.2b',
    systemPrompt: 'You are a helpful assistant. Be concise and accurate.',
  });
}, 2500);

setTimeout(() => {
  console.log('\n💭 Step 4: Think/Reason with LFM2.5\n');
  sendToolCall('rlm', {
    mode: 'think',
    sessionId: 'test-lfm2.5',
    pattern: 'analyze',
    input: 'Why is LFM2.5 important for on-device AI?',
    model: 'ollama/lfm2.5:1.2b',
  });
}, 3500);

setTimeout(() => {
  console.log('\n💰 Step 5: Check budget (should be $0 for local)\n');
  sendToolCall('state', {
    op: 'budget',
    sessionId: 'test-lfm2.5',
  });
}, 4500);

setTimeout(() => {
  server.kill();
  
  console.log('\n\n=== RESULTS ===\n');
  
  // Parse responses
  const lines = output.split('\n').filter(Boolean);
  for (const line of lines) {
    try {
      const json = JSON.parse(line);
      
      if (json.result?.content?.[0]?.text) {
        const content = json.result.content[0].text;
        
        // Try to parse as JSON
        try {
          const data = JSON.parse(content);
          
          if (data.models) {
            console.log('✅ Models listed:', data.models.length);
            const lfmModels = data.models.filter(m => m.name.includes('lfm2.5'));
            console.log('   LFM2.5 models found:', lfmModels.length);
            lfmModels.forEach(m => {
              console.log(`   - ${m.name} (${m.params || 'N/A'})`);
            });
          } else if (data.path) {
            console.log('✅ Data ingested:', data.path);
          } else if (data.response) {
            console.log('✅ LLM Response:', data.response.substring(0, 200) + '...');
          } else if (data.thoughts) {
            console.log('✅ Reasoning steps:', data.thoughts.length);
            console.log('   Conclusion:', data.conclusion.substring(0, 150) + '...');
          } else if (data.budget) {
            console.log('✅ Budget check:');
            console.log('   Used:', JSON.stringify(data.used));
            console.log('   Remaining:', JSON.stringify(data.remaining));
            console.log('   OK:', data.ok);
          }
        } catch {
          // Not JSON, show raw
          if (content.length < 500) {
            console.log('Response:', content);
          }
        }
      }
    } catch (e) {
      // Not JSON, skip
    }
  }
  
  console.log('\n✅ Test complete!\n');
}, 5500);

