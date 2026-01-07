#!/usr/bin/env node
/**
 * UNIFIED RLM MCP - v2
 * 
 * Infinite context + infinite reasoning for ANY model, ANY use case.
 * 
 * Supports:
 * - OpenAI (GPT-5.2, GPT-5.1, GPT-4o, etc.)
 * - Anthropic (Claude 4.5 Opus/Sonnet/Haiku)
 * - Google (Gemini 3 Flash/Pro)
 * - xAI (Grok 3/4)
 * - DeepSeek (V3, R1)
 * - LOCAL via Ollama (LFM2, Nemotron, Qwen, Llama, etc.)
 * 
 * Just 2 tools: `rlm` and `state`
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import * as fs from "fs/promises";
import * as path from "path";
import { existsSync, mkdirSync } from "fs";

// ============================================================================
// CONFIGURATION
// ============================================================================

const STATE_DIR = path.join(process.env.HOME || "/tmp", ".rlm-unified");
const DEBUG = process.env.RLM_DEBUG === "true";

// Provider configuration
const PROVIDER = (process.env.RLM_PROVIDER || "openai").toLowerCase();
const OLLAMA_URL = process.env.OLLAMA_URL || "http://localhost:11434";

// Default budget configuration
const DEFAULT_BUDGET = {
  maxTokens: parseInt(process.env.RLM_MAX_TOKENS || "500000"),
  maxCost: parseFloat(process.env.RLM_MAX_COST || "10.00"),
  maxIterations: parseInt(process.env.RLM_MAX_ITERATIONS || "100"),
  maxDepth: parseInt(process.env.RLM_MAX_DEPTH || "10"),
  maxTimeMs: parseInt(process.env.RLM_MAX_TIME_MS || "600000"),
};

// ============================================================================
// MODEL REGISTRY - Updated January 7, 2026
// Focused on SMALL models (1B-8B) for on-device + cheap API options
// ============================================================================

interface ModelInfo {
  provider: string;
  inputCost: number;  // per 1M tokens
  outputCost: number; // per 1M tokens
  contextWindow: number;
  tier: "cheap" | "standard" | "premium" | "local";
  params?: string;    // parameter count
}

const MODELS: Record<string, ModelInfo> = {
  // ==========================================================================
  // CLOUD APIs - PREMIUM (for synthesis/final output)
  // ==========================================================================
  
  // OpenAI - January 2026
  "gpt-5.2": { provider: "openai", inputCost: 1.75, outputCost: 14.0, contextWindow: 256000, tier: "premium" },
  "gpt-5.1": { provider: "openai", inputCost: 1.25, outputCost: 10.0, contextWindow: 256000, tier: "standard" },
  "gpt-5-mini": { provider: "openai", inputCost: 0.15, outputCost: 0.6, contextWindow: 128000, tier: "cheap", params: "~8B" },
  "gpt-4o-mini": { provider: "openai", inputCost: 0.15, outputCost: 0.6, contextWindow: 128000, tier: "cheap", params: "~8B" },
  
  // Anthropic - January 2026
  "claude-opus-4.5": { provider: "anthropic", inputCost: 5.0, outputCost: 25.0, contextWindow: 200000, tier: "premium" },
  "claude-sonnet-4.5": { provider: "anthropic", inputCost: 3.0, outputCost: 15.0, contextWindow: 200000, tier: "standard" },
  "claude-haiku-4.5": { provider: "anthropic", inputCost: 0.25, outputCost: 1.25, contextWindow: 200000, tier: "cheap", params: "~8B" },
  
  // Google Gemini - January 2026
  "gemini-3-pro": { provider: "google", inputCost: 2.0, outputCost: 8.0, contextWindow: 2000000, tier: "premium" },
  "gemini-3-flash": { provider: "google", inputCost: 0.5, outputCost: 3.0, contextWindow: 1000000, tier: "standard" },
  "gemini-2.5-flash": { provider: "google", inputCost: 0.15, outputCost: 0.6, contextWindow: 1000000, tier: "cheap" },
  
  // ==========================================================================
  // CLOUD APIs - CHEAP (for bulk processing)
  // ==========================================================================
  
  // DeepSeek - January 2026 (CHEAPEST API!)
  "deepseek-v3": { provider: "deepseek", inputCost: 0.14, outputCost: 0.28, contextWindow: 64000, tier: "cheap" },
  "deepseek-v3.2": { provider: "deepseek", inputCost: 0.027, outputCost: 0.11, contextWindow: 64000, tier: "cheap" },
  "deepseek-r1": { provider: "deepseek", inputCost: 0.55, outputCost: 2.19, contextWindow: 64000, tier: "standard" },
  
  // Z.AI GLM - January 2026 (Great for coding, $3/month plan!)
  "glm-4.7": { provider: "zhipu", inputCost: 0.5, outputCost: 2.0, contextWindow: 200000, tier: "cheap", params: "355B/32B active" },
  "glm-4.6": { provider: "zhipu", inputCost: 0.3, outputCost: 1.2, contextWindow: 128000, tier: "cheap" },
  "glm-4.5": { provider: "zhipu", inputCost: 0.2, outputCost: 0.8, contextWindow: 128000, tier: "cheap" },
  
  // MiniMax - January 2026 (10B active params, great for coding!)
  "minimax-m2.1": { provider: "minimax", inputCost: 0.12, outputCost: 0.48, contextWindow: 196608, tier: "cheap", params: "10B active" },
  "minimax-m2": { provider: "minimax", inputCost: 0.3, outputCost: 1.2, contextWindow: 200000, tier: "cheap" },
  
  // xAI Grok - January 2026
  "grok-4.1-fast": { provider: "xai", inputCost: 0.2, outputCost: 0.5, contextWindow: 131000, tier: "cheap" },
  "grok-3": { provider: "xai", inputCost: 3.0, outputCost: 15.0, contextWindow: 131000, tier: "standard" },
  
  // ==========================================================================
  // LOCAL via Ollama - FREE (on-device, small models 1B-8B)
  // ==========================================================================
  
  // Qwen 3 Family - Alibaba (EXCELLENT for small models)
  "ollama/qwen3:0.6b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 32000, tier: "local", params: "0.6B" },
  "ollama/qwen3:1.7b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 32000, tier: "local", params: "1.7B" },
  "ollama/qwen3:4b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 32000, tier: "local", params: "4B" },
  "ollama/qwen3:8b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 32000, tier: "local", params: "8B" },
  "ollama/qwen2.5:3b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 32000, tier: "local", params: "3B" },
  "ollama/qwen2.5:7b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 32000, tier: "local", params: "7B" },
  "ollama/qwen2.5-coder:3b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 32000, tier: "local", params: "3B" },
  "ollama/qwen2.5-coder:7b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 32000, tier: "local", params: "7B" },
  
  // DeepSeek R1 Distilled - Local reasoning models
  "ollama/deepseek-r1:1.5b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 128000, tier: "local", params: "1.5B" },
  "ollama/deepseek-r1:7b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 128000, tier: "local", params: "7B" },
  "ollama/deepseek-r1:8b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 128000, tier: "local", params: "8B" },
  
  // Liquid Foundation Models (LFM) - FASTEST on-device!
  // LFM2.5 - Released Jan 5, 2026! 28T tokens pretraining, QAT optimized
  "ollama/lfm2.5:1.2b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 32000, tier: "local", params: "1.2B (NEW Jan 2026)" },
  "ollama/lfm2.5-audio": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 32000, tier: "local", params: "1.5B audio, 8x faster" },
  "ollama/lfm2.5-vl:1.6b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 32000, tier: "local", params: "1.6B vision" },
  // LFM2 - Still great
  "ollama/lfm2:350m": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 125000, tier: "local", params: "350M" },
  "ollama/lfm2:700m": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 125000, tier: "local", params: "700M" },
  "ollama/lfm2:1.2b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 32000, tier: "local", params: "1.2B" },
  "ollama/lfm2:2.6b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 125000, tier: "local", params: "2.6B" },
  "ollama/lfm2:8b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 125000, tier: "local", params: "8B MoE, 1.5B active" },
  
  // NVIDIA Nemotron - Agentic models
  "ollama/nemotron-3-nano": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 32000, tier: "local", params: "~4B" },
  
  // Phi-4 - Microsoft (great reasoning for size)
  "ollama/phi4": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 16000, tier: "local", params: "14B" },
  "ollama/phi4-mini": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 16000, tier: "local", params: "3.8B" },
  
  // Gemma 3 - Google (function calling specialist)
  "ollama/gemma3:1b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 8000, tier: "local", params: "1B" },
  "ollama/gemma3:4b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 8000, tier: "local", params: "4B" },
  "ollama/functiongemma": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 8000, tier: "local", params: "270M" },
  
  // Llama 3.3 - Meta
  "ollama/llama3.3:3b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 128000, tier: "local", params: "3B" },
  "ollama/llama3.3:8b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 128000, tier: "local", params: "8B" },
  
  // SmolLM2 - Hugging Face (tiny but capable)
  "ollama/smollm2:135m": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 8000, tier: "local", params: "135M" },
  "ollama/smollm2:360m": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 8000, tier: "local", params: "360M" },
  "ollama/smollm2:1.7b": { provider: "ollama", inputCost: 0, outputCost: 0, contextWindow: 8000, tier: "local", params: "1.7B" },
};

// Model selection based on tier - focused on SMALL models
const MODEL_TIERS = {
  // Cheapest API: DeepSeek V3.2 at $0.027/1M input
  cheap: process.env.RLM_MODEL_CHEAP || "deepseek-v3.2",
  // Standard: MiniMax M2.1 (10B active, great for coding)
  standard: process.env.RLM_MODEL || "minimax-m2.1",
  // Premium: Claude for synthesis
  premium: process.env.RLM_MODEL_PREMIUM || "claude-sonnet-4.5",
  // Local: Qwen3 4B (best quality/size ratio)
  local: process.env.RLM_MODEL_LOCAL || "ollama/qwen3:4b",
  // Tiny: For edge devices (LFM2.5 1.2B - NEW Jan 2026!)
  tiny: process.env.RLM_MODEL_TINY || "ollama/lfm2.5:1.2b",
};

// Ensure state directory exists
if (!existsSync(STATE_DIR)) {
  mkdirSync(STATE_DIR, { recursive: true });
}

// ============================================================================
// TYPES
// ============================================================================

interface Budget {
  maxTokens: number;
  maxCost: number;
  maxIterations: number;
  maxDepth: number;
  maxTimeMs: number;
}

interface SessionMeta {
  id: string;
  createdAt: number;
  lastAccessedAt: number;
  tokensUsed: number;
  costUsed: number;
  iterationsUsed: number;
  currentDepth: number;
  startTime: number;
  budget: Budget;
}

interface Session {
  meta: SessionMeta;
  state: Map<string, unknown>;
  paths: string[];
}

const sessions = new Map<string, Session>();

// ============================================================================
// SESSION MANAGEMENT
// ============================================================================

function getSessionDir(sessionId: string): string {
  return path.join(STATE_DIR, "sessions", sessionId);
}

async function getOrCreateSession(sessionId: string): Promise<Session> {
  if (sessions.has(sessionId)) {
    const session = sessions.get(sessionId)!;
    session.meta.lastAccessedAt = Date.now();
    return session;
  }

  const sessionDir = getSessionDir(sessionId);
  const metaPath = path.join(sessionDir, "_meta.json");
  const statePath = path.join(sessionDir, "_state.json");

  for (const dir of ["input", "chunks", "output"]) {
    const p = path.join(sessionDir, dir);
    if (!existsSync(p)) mkdirSync(p, { recursive: true });
  }

  let meta: SessionMeta;
  if (existsSync(metaPath)) {
    meta = JSON.parse(await fs.readFile(metaPath, "utf-8"));
  } else {
    meta = {
      id: sessionId,
      createdAt: Date.now(),
      lastAccessedAt: Date.now(),
      tokensUsed: 0,
      costUsed: 0,
      iterationsUsed: 0,
      currentDepth: 0,
      startTime: Date.now(),
      budget: { ...DEFAULT_BUDGET },
    };
    await fs.writeFile(metaPath, JSON.stringify(meta, null, 2));
  }

  let stateData: Record<string, unknown> = {};
  if (existsSync(statePath)) {
    stateData = JSON.parse(await fs.readFile(statePath, "utf-8"));
  }

  const session: Session = {
    meta,
    state: new Map(Object.entries(stateData)),
    paths: [],
  };

  sessions.set(sessionId, session);
  return session;
}

async function saveSession(session: Session): Promise<void> {
  const sessionDir = getSessionDir(session.meta.id);
  const metaPath = path.join(sessionDir, "_meta.json");
  const statePath = path.join(sessionDir, "_state.json");

  await fs.writeFile(metaPath, JSON.stringify(session.meta, null, 2));
  await fs.writeFile(
    statePath,
    JSON.stringify(Object.fromEntries(session.state), null, 2)
  );
}

// ============================================================================
// BUDGET TRACKING
// ============================================================================

function checkBudget(session: Session): { ok: boolean; reason?: string; remaining: Record<string, number> } {
  const { meta } = session;
  const { budget } = meta;

  const remaining = {
    tokens: budget.maxTokens - meta.tokensUsed,
    cost: budget.maxCost - meta.costUsed,
    iterations: budget.maxIterations - meta.iterationsUsed,
    timeMs: budget.maxTimeMs - (Date.now() - meta.startTime),
  };

  if (remaining.tokens <= 0) return { ok: false, reason: "Token budget exhausted", remaining };
  if (remaining.cost <= 0) return { ok: false, reason: "Cost budget exhausted", remaining };
  if (remaining.iterations <= 0) return { ok: false, reason: "Iteration limit reached", remaining };
  if (remaining.timeMs <= 0) return { ok: false, reason: "Time budget exhausted", remaining };

  return { ok: true, remaining };
}

function trackUsage(
  session: Session,
  model: string,
  inputTokens: number,
  outputTokens: number
): void {
  const modelInfo = MODELS[model] || MODELS["gpt-4o-mini"];
  const cost = (inputTokens * modelInfo.inputCost + outputTokens * modelInfo.outputCost) / 1_000_000;

  session.meta.tokensUsed += inputTokens + outputTokens;
  session.meta.costUsed += cost;
  session.meta.iterationsUsed += 1;

  if (DEBUG) {
    console.error(
      `[RLM] ${model}: +${inputTokens + outputTokens} tokens, +$${cost.toFixed(4)}, ` +
      `total: ${session.meta.tokensUsed} tokens, $${session.meta.costUsed.toFixed(4)}`
    );
  }
}

// ============================================================================
// MULTI-PROVIDER LLM CLIENT
// ============================================================================

async function callLLM(
  model: string,
  messages: Array<{ role: string; content: string }>,
): Promise<{ content: string; inputTokens: number; outputTokens: number }> {
  const modelInfo = MODELS[model];
  if (!modelInfo) {
    throw new Error(`Unknown model: ${model}. Available: ${Object.keys(MODELS).join(", ")}`);
  }

  const provider = modelInfo.provider;

  if (provider === "ollama") {
    return callOllama(model.replace("ollama/", ""), messages);
  } else if (provider === "openai") {
    return callOpenAI(model, messages);
  } else if (provider === "anthropic") {
    return callAnthropic(model, messages);
  } else if (provider === "google") {
    return callGoogle(model, messages);
  } else if (provider === "deepseek") {
    return callDeepSeek(model, messages);
  } else if (provider === "xai") {
    return callXAI(model, messages);
  } else if (provider === "zhipu") {
    return callZhipu(model, messages);
  } else if (provider === "minimax") {
    return callMiniMax(model, messages);
  }

  throw new Error(`Unsupported provider: ${provider}`);
}

// OpenAI
async function callOpenAI(
  model: string,
  messages: Array<{ role: string; content: string }>
): Promise<{ content: string; inputTokens: number; outputTokens: number }> {
  const { default: OpenAI } = await import("openai");
  const client = new OpenAI();
  
  const response = await client.chat.completions.create({
    model,
    messages: messages as any,
    temperature: 0.7,
  });

  return {
    content: response.choices[0]?.message?.content || "",
    inputTokens: response.usage?.prompt_tokens || 0,
    outputTokens: response.usage?.completion_tokens || 0,
  };
}

// Anthropic
async function callAnthropic(
  model: string,
  messages: Array<{ role: string; content: string }>
): Promise<{ content: string; inputTokens: number; outputTokens: number }> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error("ANTHROPIC_API_KEY not set");

  // Extract system message
  const systemMsg = messages.find(m => m.role === "system");
  const otherMsgs = messages.filter(m => m.role !== "system");

  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2024-01-01",
    },
    body: JSON.stringify({
      model,
      max_tokens: 4096,
      system: systemMsg?.content,
      messages: otherMsgs.map(m => ({ role: m.role, content: m.content })),
    }),
  });

  const data = await response.json() as any;
  
  return {
    content: data.content?.[0]?.text || "",
    inputTokens: data.usage?.input_tokens || 0,
    outputTokens: data.usage?.output_tokens || 0,
  };
}

// Google Gemini
async function callGoogle(
  model: string,
  messages: Array<{ role: string; content: string }>
): Promise<{ content: string; inputTokens: number; outputTokens: number }> {
  const apiKey = process.env.GOOGLE_API_KEY;
  if (!apiKey) throw new Error("GOOGLE_API_KEY not set");

  const contents = messages.map(m => ({
    role: m.role === "assistant" ? "model" : "user",
    parts: [{ text: m.content }],
  }));

  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ contents }),
    }
  );

  const data = await response.json() as any;
  
  return {
    content: data.candidates?.[0]?.content?.parts?.[0]?.text || "",
    inputTokens: data.usageMetadata?.promptTokenCount || 0,
    outputTokens: data.usageMetadata?.candidatesTokenCount || 0,
  };
}

// DeepSeek
async function callDeepSeek(
  model: string,
  messages: Array<{ role: string; content: string }>
): Promise<{ content: string; inputTokens: number; outputTokens: number }> {
  const apiKey = process.env.DEEPSEEK_API_KEY;
  if (!apiKey) throw new Error("DEEPSEEK_API_KEY not set");

  const response = await fetch("https://api.deepseek.com/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: model.replace("deepseek-", ""),
      messages,
    }),
  });

  const data = await response.json() as any;
  
  return {
    content: data.choices?.[0]?.message?.content || "",
    inputTokens: data.usage?.prompt_tokens || 0,
    outputTokens: data.usage?.completion_tokens || 0,
  };
}

// xAI Grok
async function callXAI(
  model: string,
  messages: Array<{ role: string; content: string }>
): Promise<{ content: string; inputTokens: number; outputTokens: number }> {
  const apiKey = process.env.XAI_API_KEY;
  if (!apiKey) throw new Error("XAI_API_KEY not set");

  const response = await fetch("https://api.x.ai/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${apiKey}`,
    },
    body: JSON.stringify({ model, messages }),
  });

  const data = await response.json() as any;
  
  return {
    content: data.choices?.[0]?.message?.content || "",
    inputTokens: data.usage?.prompt_tokens || 0,
    outputTokens: data.usage?.completion_tokens || 0,
  };
}

// Ollama (LOCAL - FREE)
async function callOllama(
  model: string,
  messages: Array<{ role: string; content: string }>
): Promise<{ content: string; inputTokens: number; outputTokens: number }> {
  const response = await fetch(`${OLLAMA_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model,
      messages,
      stream: false,
    }),
  });

  const data = await response.json() as any;
  
  return {
    content: data.message?.content || "",
    inputTokens: data.prompt_eval_count || 0,
    outputTokens: data.eval_count || 0,
  };
}

// Z.AI / Zhipu GLM (GLM-4.7, GLM-4.6, etc.)
async function callZhipu(
  model: string,
  messages: Array<{ role: string; content: string }>
): Promise<{ content: string; inputTokens: number; outputTokens: number }> {
  const apiKey = process.env.ZHIPU_API_KEY || process.env.ZAI_API_KEY;
  if (!apiKey) throw new Error("ZHIPU_API_KEY or ZAI_API_KEY not set");

  const response = await fetch("https://open.bigmodel.cn/api/paas/v4/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: model.replace("glm-", "GLM-"),
      messages,
    }),
  });

  const data = await response.json() as any;
  
  return {
    content: data.choices?.[0]?.message?.content || "",
    inputTokens: data.usage?.prompt_tokens || 0,
    outputTokens: data.usage?.completion_tokens || 0,
  };
}

// MiniMax (M2.1, M2)
async function callMiniMax(
  model: string,
  messages: Array<{ role: string; content: string }>
): Promise<{ content: string; inputTokens: number; outputTokens: number }> {
  const apiKey = process.env.MINIMAX_API_KEY;
  if (!apiKey) throw new Error("MINIMAX_API_KEY not set");

  // MiniMax uses OpenAI-compatible API
  const response = await fetch("https://api.minimax.chat/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: model.replace("minimax-", "MiniMax-"),
      messages,
    }),
  });

  const data = await response.json() as any;
  
  return {
    content: data.choices?.[0]?.message?.content || "",
    inputTokens: data.usage?.prompt_tokens || 0,
    outputTokens: data.usage?.completion_tokens || 0,
  };
}

// ============================================================================
// CORE FUNCTIONS
// ============================================================================

function selectModel(session: Session, preferredModel?: string): string {
  if (preferredModel && MODELS[preferredModel]) {
    return preferredModel;
  }

  const budgetCheck = checkBudget(session);
  
  // If budget is tight, use cheaper model
  if (budgetCheck.remaining.cost < 1) {
    return MODEL_TIERS.cheap;
  }
  
  // If local is preferred and available
  if (PROVIDER === "ollama" || PROVIDER === "local") {
    return MODEL_TIERS.local;
  }

  return MODEL_TIERS.standard;
}

/**
 * Ingest: Store data externally
 */
async function ingest(
  session: Session,
  data: string | object,
  name?: string
): Promise<{ path: string; size: number }> {
  const sessionDir = getSessionDir(session.meta.id);
  const timestamp = Date.now();
  const fileName = name || `data_${timestamp}`;
  const isJson = typeof data === "object";
  const ext = isJson ? ".json" : ".txt";
  const filePath = path.join(sessionDir, "input", `${fileName}${ext}`);

  const content = isJson ? JSON.stringify(data, null, 2) : String(data);
  await fs.writeFile(filePath, content, "utf-8");
  session.paths.push(filePath);

  if (DEBUG) console.error(`[RLM] Ingested ${content.length} bytes to ${filePath}`);

  return { path: filePath, size: content.length };
}

/**
 * Chunk: Split large data into pieces
 */
async function chunk(
  session: Session,
  inputPath: string,
  chunkSize: number = 4000,
  overlap: number = 200
): Promise<{ chunks: string[]; count: number }> {
  const content = await fs.readFile(inputPath, "utf-8");
  const sessionDir = getSessionDir(session.meta.id);
  const baseName = path.basename(inputPath, path.extname(inputPath));
  
  const chunks: string[] = [];
  let start = 0;
  let chunkIndex = 0;

  while (start < content.length) {
    const end = Math.min(start + chunkSize, content.length);
    const chunkContent = content.slice(start, end);
    
    const chunkPath = path.join(sessionDir, "chunks", `${baseName}_chunk_${chunkIndex}.txt`);
    await fs.writeFile(chunkPath, chunkContent, "utf-8");
    chunks.push(chunkPath);
    
    start = end - overlap;
    if (start >= content.length - overlap) break;
    chunkIndex++;
  }

  if (DEBUG) console.error(`[RLM] Split into ${chunks.length} chunks`);

  return { chunks, count: chunks.length };
}

/**
 * Process: Recursive LLM call
 */
async function processChunk(
  session: Session,
  prompt: string,
  contextPaths?: string[],
  model?: string,
  systemPrompt?: string
): Promise<{ response: string; tokensUsed: number; model: string; cost: number }> {
  const budgetCheck = checkBudget(session);
  if (!budgetCheck.ok) {
    return {
      response: `[BUDGET EXCEEDED] ${budgetCheck.reason}. Remaining: ${JSON.stringify(budgetCheck.remaining)}`,
      tokensUsed: 0,
      model: "none",
      cost: 0,
    };
  }

  // Load context
  let contextContent = "";
  if (contextPaths && contextPaths.length > 0) {
    for (const p of contextPaths) {
      try {
        const content = await fs.readFile(p, "utf-8");
        const fileName = path.basename(p);
        contextContent += `\n--- ${fileName} ---\n${content}\n`;
      } catch (e) {
        contextContent += `\n--- Error loading ${p}: ${e} ---\n`;
      }
    }
  }

  // Build messages
  const messages: Array<{ role: string; content: string }> = [];
  
  messages.push({
    role: "system",
    content: systemPrompt || "You are a helpful assistant. Process the given context and task efficiently. Be concise but thorough.",
  });

  const fullPrompt = contextContent
    ? `${prompt}\n\n--- CONTEXT ---\n${contextContent}`
    : prompt;
  messages.push({ role: "user", content: fullPrompt });

  // Select model
  const useModel = selectModel(session, model);

  if (DEBUG) console.error(`[RLM] Processing with ${useModel}`);

  const result = await callLLM(useModel, messages);

  // Track usage
  trackUsage(session, useModel, result.inputTokens, result.outputTokens);

  const modelInfo = MODELS[useModel] || MODELS["gpt-4o-mini"];
  const cost = (result.inputTokens * modelInfo.inputCost + result.outputTokens * modelInfo.outputCost) / 1_000_000;

  return {
    response: result.content,
    tokensUsed: result.inputTokens + result.outputTokens,
    model: useModel,
    cost,
  };
}

/**
 * Search: Find content in externalized data
 */
async function search(
  session: Session,
  query: string,
  paths?: string[],
  maxResults: number = 20
): Promise<{ matches: Array<{ path: string; line: number; content: string }> }> {
  const searchPaths = paths || session.paths;
  const matches: Array<{ path: string; line: number; content: string }> = [];
  const regex = new RegExp(query, "gi");

  for (const filePath of searchPaths) {
    try {
      const content = await fs.readFile(filePath, "utf-8");
      const lines = content.split("\n");

      for (let i = 0; i < lines.length; i++) {
        if (regex.test(lines[i])) {
          matches.push({
            path: filePath,
            line: i + 1,
            content: lines[i].trim().slice(0, 200),
          });
          if (matches.length >= maxResults) break;
        }
        regex.lastIndex = 0;
      }
      if (matches.length >= maxResults) break;
    } catch {
      // Skip
    }
  }

  return { matches };
}

/**
 * Synthesize: Combine results
 */
async function synthesize(
  session: Session,
  task: string,
  resultPaths: string[],
  model?: string
): Promise<{ synthesis: string; tokensUsed: number; cost: number }> {
  let combinedContent = "";
  for (const p of resultPaths) {
    try {
      const content = await fs.readFile(p, "utf-8");
      combinedContent += `\n--- Result from ${path.basename(p)} ---\n${content}\n`;
    } catch {
      // Skip
    }
  }

  // Use premium model for synthesis
  const useModel = model || MODEL_TIERS.premium;

  const result = await processChunk(
    session,
    `${task}\n\nCombine and synthesize the following results into a coherent response:\n${combinedContent}`,
    [],
    useModel,
    "You are synthesizing multiple analysis results. Create a unified, coherent output."
  );

  const sessionDir = getSessionDir(session.meta.id);
  const outputPath = path.join(sessionDir, "output", `synthesis_${Date.now()}.txt`);
  await fs.writeFile(outputPath, result.response, "utf-8");

  return { synthesis: result.response, tokensUsed: result.tokensUsed, cost: result.cost };
}

/**
 * Think: Structured reasoning
 */
async function think(
  session: Session,
  pattern: "decompose" | "analyze" | "evaluate" | "plan" | "chain",
  input: string,
  contextPaths?: string[],
  steps?: number
): Promise<{ thoughts: string[]; conclusion: string; tokensUsed: number; cost: number }> {
  const patterns: Record<string, string> = {
    decompose: `Break down this problem into smaller, manageable sub-problems:\n${input}`,
    analyze: `Analyze this thoroughly - identify key components, patterns, and insights:\n${input}`,
    evaluate: `Evaluate this critically - strengths, weaknesses, risks, recommendation:\n${input}`,
    plan: `Create an actionable plan with clear goals, steps, and milestones:\n${input}`,
    chain: `Think through this step by step:\n${input}`,
  };

  const prompt = patterns[pattern] || patterns.analyze;
  const thoughts: string[] = [];
  let totalTokens = 0;
  let totalCost = 0;

  const iterations = pattern === "chain" ? (steps || 3) : 1;
  let lastResult = input;

  for (let i = 0; i < iterations; i++) {
    const budgetCheck = checkBudget(session);
    if (!budgetCheck.ok) {
      thoughts.push(`[BUDGET EXCEEDED at step ${i + 1}]`);
      break;
    }

    const result = await processChunk(
      session,
      i === 0 ? prompt : `Continue from previous step:\n${lastResult}\n\nNext step:`,
      contextPaths,
      MODEL_TIERS.standard,
      "You are a structured reasoning assistant. Think clearly and systematically."
    );

    thoughts.push(result.response);
    lastResult = result.response;
    totalTokens += result.tokensUsed;
    totalCost += result.cost;
  }

  return {
    thoughts,
    conclusion: thoughts[thoughts.length - 1] || "",
    tokensUsed: totalTokens,
    cost: totalCost,
  };
}

// ============================================================================
// TOOL SCHEMAS
// ============================================================================

const RlmSchema = z.object({
  mode: z.enum(["ingest", "chunk", "process", "search", "synthesize", "think", "models"]),
  sessionId: z.string().optional().default("default"),
  data: z.union([z.string(), z.record(z.unknown())]).optional(),
  name: z.string().optional(),
  inputPath: z.string().optional(),
  chunkSize: z.number().optional(),
  overlap: z.number().optional(),
  prompt: z.string().optional(),
  contextPaths: z.array(z.string()).optional(),
  model: z.string().optional(),
  systemPrompt: z.string().optional(),
  query: z.string().optional(),
  paths: z.array(z.string()).optional(),
  maxResults: z.number().optional(),
  task: z.string().optional(),
  resultPaths: z.array(z.string()).optional(),
  pattern: z.enum(["decompose", "analyze", "evaluate", "plan", "chain"]).optional(),
  input: z.string().optional(),
  steps: z.number().optional(),
});

const StateSchema = z.object({
  op: z.enum(["get", "set", "list", "clear", "budget", "reset", "export"]),
  sessionId: z.string().optional().default("default"),
  key: z.string().optional(),
  value: z.unknown().optional(),
  path: z.string().optional(),
  budget: z.object({
    maxTokens: z.number().optional(),
    maxCost: z.number().optional(),
    maxIterations: z.number().optional(),
    maxDepth: z.number().optional(),
    maxTimeMs: z.number().optional(),
  }).optional(),
});

// ============================================================================
// MCP SERVER
// ============================================================================

const server = new Server(
  { name: "unified-rlm-mcp", version: "2.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "rlm",
      description: `Unified RLM - Infinite context & reasoning for ANY model.

MODES:
- ingest: Store data externally
- chunk: Split large data
- process: Recursive LLM call (auto-selects best model for budget)
- search: Find in externalized data
- synthesize: Combine results
- think: Structured reasoning (decompose/analyze/evaluate/plan/chain)
- models: List available models with pricing

SUPPORTED MODELS:
- OpenAI: gpt-5.2, gpt-5.1, gpt-4o-mini
- Anthropic: claude-opus-4.5, claude-haiku-4.5
- Google: gemini-3-flash, gemini-2.5-flash
- DeepSeek: deepseek-v3 (CHEAPEST: $0.14/1M)
- xAI: grok-4, grok-4.1-fast
- LOCAL: ollama/llama3.3, ollama/qwen2.5, ollama/lfm2 (FREE)

BUDGET: Auto-tracks tokens & cost. Switches to cheaper models when low.`,
      inputSchema: {
        type: "object",
        properties: {
          mode: { type: "string", enum: ["ingest", "chunk", "process", "search", "synthesize", "think", "models"] },
          sessionId: { type: "string" },
          data: { description: "Data to ingest" },
          name: { type: "string" },
          inputPath: { type: "string" },
          chunkSize: { type: "number" },
          overlap: { type: "number" },
          prompt: { type: "string" },
          contextPaths: { type: "array", items: { type: "string" } },
          model: { type: "string", description: "Model to use (e.g., claude-haiku-4.5, ollama/llama3.3)" },
          systemPrompt: { type: "string" },
          query: { type: "string" },
          paths: { type: "array", items: { type: "string" } },
          maxResults: { type: "number" },
          task: { type: "string" },
          resultPaths: { type: "array", items: { type: "string" } },
          pattern: { type: "string", enum: ["decompose", "analyze", "evaluate", "plan", "chain"] },
          input: { type: "string" },
          steps: { type: "number" },
        },
        required: ["mode"],
      },
    },
    {
      name: "state",
      description: `Manage persistent state and budget.

OPS:
- get/set: Key-value storage
- list: List all keys
- budget: Check/set budget (tokens, cost, iterations)
- reset: Reset session
- export: Export to file`,
      inputSchema: {
        type: "object",
        properties: {
          op: { type: "string", enum: ["get", "set", "list", "clear", "budget", "reset", "export"] },
          sessionId: { type: "string" },
          key: { type: "string" },
          value: {},
          path: { type: "string" },
          budget: { type: "object" },
        },
        required: ["op"],
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "rlm") {
      const parsed = RlmSchema.parse(args);
      const session = await getOrCreateSession(parsed.sessionId);

      let result: unknown;

      switch (parsed.mode) {
        case "models":
          result = {
            models: Object.entries(MODELS).map(([name, info]) => ({
              name,
              provider: info.provider,
              inputCost: `$${info.inputCost}/1M`,
              outputCost: `$${info.outputCost}/1M`,
              contextWindow: info.contextWindow,
              tier: info.tier,
            })),
            currentTiers: MODEL_TIERS,
          };
          break;

        case "ingest":
          if (!parsed.data) throw new Error("data required");
          result = await ingest(session, parsed.data, parsed.name);
          break;

        case "chunk":
          if (!parsed.inputPath) throw new Error("inputPath required");
          result = await chunk(session, parsed.inputPath, parsed.chunkSize, parsed.overlap);
          break;

        case "process":
          if (!parsed.prompt) throw new Error("prompt required");
          result = await processChunk(session, parsed.prompt, parsed.contextPaths, parsed.model, parsed.systemPrompt);
          break;

        case "search":
          if (!parsed.query) throw new Error("query required");
          result = await search(session, parsed.query, parsed.paths, parsed.maxResults);
          break;

        case "synthesize":
          if (!parsed.task || !parsed.resultPaths) throw new Error("task and resultPaths required");
          result = await synthesize(session, parsed.task, parsed.resultPaths, parsed.model);
          break;

        case "think":
          if (!parsed.pattern || !parsed.input) throw new Error("pattern and input required");
          result = await think(session, parsed.pattern, parsed.input, parsed.contextPaths, parsed.steps);
          break;
      }

      await saveSession(session);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }

    if (name === "state") {
      const parsed = StateSchema.parse(args);
      const session = await getOrCreateSession(parsed.sessionId);

      let result: unknown;

      switch (parsed.op) {
        case "get":
          if (!parsed.key) throw new Error("key required");
          result = { value: session.state.get(parsed.key) };
          break;

        case "set":
          if (!parsed.key) throw new Error("key required");
          session.state.set(parsed.key, parsed.value);
          result = { success: true, key: parsed.key };
          break;

        case "list":
          result = { keys: Array.from(session.state.keys()), count: session.state.size };
          break;

        case "clear":
          session.state.clear();
          result = { success: true };
          break;

        case "budget":
          if (parsed.budget) {
            Object.assign(session.meta.budget, parsed.budget);
          }
          const check = checkBudget(session);
          result = {
            budget: session.meta.budget,
            used: {
              tokens: session.meta.tokensUsed,
              cost: `$${session.meta.costUsed.toFixed(4)}`,
              iterations: session.meta.iterationsUsed,
              timeMs: Date.now() - session.meta.startTime,
            },
            remaining: {
              tokens: check.remaining.tokens,
              cost: `$${check.remaining.cost.toFixed(4)}`,
              iterations: check.remaining.iterations,
              timeMs: check.remaining.timeMs,
            },
            ok: check.ok,
          };
          break;

        case "reset":
          session.state.clear();
          session.meta.tokensUsed = 0;
          session.meta.costUsed = 0;
          session.meta.iterationsUsed = 0;
          session.meta.startTime = Date.now();
          result = { success: true };
          break;

        case "export":
          const exportPath = parsed.path || path.join(getSessionDir(session.meta.id), "export.json");
          const exportData = {
            meta: session.meta,
            state: Object.fromEntries(session.state),
            paths: session.paths,
          };
          await fs.writeFile(exportPath, JSON.stringify(exportData, null, 2));
          result = { success: true, path: exportPath };
          break;
      }

      await saveSession(session);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }

    throw new Error(`Unknown tool: ${name}`);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return { content: [{ type: "text", text: `Error: ${message}` }], isError: true };
  }
});

// ============================================================================
// START
// ============================================================================

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);

  if (DEBUG) {
    console.error("[UNIFIED-RLM v2] Server started");
    console.error(`[UNIFIED-RLM v2] State: ${STATE_DIR}`);
    console.error(`[UNIFIED-RLM v2] Provider: ${PROVIDER}`);
    console.error(`[UNIFIED-RLM v2] Models: cheap=${MODEL_TIERS.cheap}, standard=${MODEL_TIERS.standard}, premium=${MODEL_TIERS.premium}`);
    if (PROVIDER === "ollama") {
      console.error(`[UNIFIED-RLM v2] Ollama URL: ${OLLAMA_URL}`);
    }
  }
}

main().catch((error) => {
  console.error("Fatal:", error);
  process.exit(1);
});
