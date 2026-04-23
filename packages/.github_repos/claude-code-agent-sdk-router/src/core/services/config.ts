// ConfigService — loads config from ~/.ccasr/config.json
// Interpolates $ENV_VAR references in api_key fields.
// Validates provider names against the allowed set.
// Fails hard on invalid config — no silent defaults.

import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';
import JSON5 from 'json5';
import type { AppConfig, AgentsConfig, GatewayOptions, ModelTier, ProviderConfig, RouterConfig, SubagentDefinition, SupportedProvider } from '../types';
import { SUPPORTED_PROVIDERS } from '../types';
import * as crypto from 'crypto';

// Provider base URLs — exported for gateway mode and cli/constants
export const PROVIDER_BASE_URLS: Record<SupportedProvider, string> = {
  anthropic: 'https://api.anthropic.com',
  openrouter: 'https://openrouter.ai/api/v1/chat/completions',
  gemini: 'https://generativelanguage.googleapis.com/v1beta/models/',
  openai: 'https://api.openai.com/v1/chat/completions',
  groq: 'https://api.groq.com/openai/v1/chat/completions',
  mistral: 'https://api.mistral.ai/v1/chat/completions',
  ollama: 'http://localhost:11434/v1/chat/completions',
  minimax: 'https://api.minimax.io/anthropic',
  glm: 'https://api.z.ai/api/anthropic',
};

const MODEL_TIER_PATTERNS: Array<{ tier: ModelTier; match: string }> = [
  { tier: 'opus',   match: 'opus' },
  { tier: 'haiku',  match: 'haiku' },
  { tier: 'sonnet', match: 'sonnet' },
];

const CONFIG_DIR = join(homedir(), '.ccasr');
const CONFIG_FILE = join(CONFIG_DIR, 'config.json');

const DEFAULT_CONFIG: Partial<AppConfig> = {
  LOG: false,
  API_TIMEOUT_MS: 300_000,
  PORT: 3456,
};

/** Interpolate $ENV_VAR references in config values */
function interpolateEnvVar(value: string): string {
  if (value.startsWith('$')) {
    const envName = value.substring(1);
    const envValue = process.env[envName];
    if (!envValue) {
      throw new Error(`Environment variable ${envName} is not set (referenced in config api_key)`);
    }
    return envValue;
  }
  return value;
}

export class ConfigService {
  private config: AppConfig;
  readonly configPath: string;
  readonly mode: 'standard' | 'gateway';
  private subagents = new Map<string, SubagentDefinition>();  // hash → definition

  constructor(configPath?: string, activeRouteOverride?: string);
  constructor(prebuilt: AppConfig, mode: 'gateway');
  constructor(configPathOrPrebuilt?: string | AppConfig, activeRouteOrMode?: string) {
    if (typeof configPathOrPrebuilt === 'object' && configPathOrPrebuilt !== null) {
      // Gateway mode: accept pre-built AppConfig directly
      this.config = configPathOrPrebuilt;
      this.configPath = '(gateway)';
      this.mode = 'gateway';
    } else {
      this.configPath = configPathOrPrebuilt || CONFIG_FILE;
      this.config = this.loadAndValidate(this.configPath, activeRouteOrMode);
      this.mode = 'standard';
    }
  }

  /** Create a ConfigService for gateway mode — no config file needed */
  static forGateway(options: GatewayOptions = {}): ConfigService {
    // Build providers: all 7 with default base URLs, empty keys unless overridden
    const providers: ProviderConfig[] = SUPPORTED_PROVIDERS.map((name) => ({
      name,
      api_base_url: options.providerUrls?.[name] || PROVIDER_BASE_URLS[name],
      api_key: options.providers?.[name]
        ? interpolateEnvVar(options.providers[name]!)
        : '',
    }));

    const config: AppConfig = {
      LOG: false,
      API_TIMEOUT_MS: options.timeoutMs ?? 300_000,
      PORT: options.port ?? 0,
      PROXY_URL: options.proxyUrl,
      LOG_FILE: options.logToFile ?? false,
      LOG_MAX_SIZE: '10m',
      LOG_MAX_FILES: 5,
      Providers: providers,
      Routes: { gateway: { sonnet: 'anthropic,claude-sonnet-4-20250514' } },
      ActiveRoute: 'gateway',
      Router: { sonnet: 'anthropic,claude-sonnet-4-20250514' },
    };

    return new ConfigService(config, 'gateway');
  }

  private loadAndValidate(configPath: string, activeRouteOverride?: string): AppConfig {
    if (!existsSync(configPath)) {
      throw new Error(
        `Config file not found: ${configPath}\n` +
        `Create it with: mkdir -p ~/.ccasr && cp config.example.json ~/.ccasr/config.json`,
      );
    }

    let raw: any;
    try {
      const content = readFileSync(configPath, 'utf-8');
      raw = JSON5.parse(content);
    } catch (err: any) {
      throw new Error(`Failed to parse config file ${configPath}: ${err.message}`);
    }

    const config: AppConfig = {
      LOG: raw.LOG ?? DEFAULT_CONFIG.LOG!,
      API_TIMEOUT_MS: raw.API_TIMEOUT_MS ?? DEFAULT_CONFIG.API_TIMEOUT_MS!,
      PORT: raw.PORT ?? DEFAULT_CONFIG.PORT!,
      PROXY_URL: raw.PROXY_URL,
      LOG_FILE: raw.LOG_FILE !== false,         // default true
      LOG_MAX_SIZE: raw.LOG_MAX_SIZE || '10m',
      LOG_MAX_FILES: raw.LOG_MAX_FILES || 5,
      Providers: [],
      Routes: {},
      ActiveRoute: '',
      Router: { sonnet: '' },
    };

    // --- Parse Routes first (to know which providers are needed) ---
    // New format: Routes: { "direct": { sonnet, opus?, haiku? }, ... } + ActiveRoute
    // Old format: Router: { sonnet, opus?, haiku? }
    if (raw.Routes && typeof raw.Routes === 'object') {
      // New format
      for (const [routeName, routeSet] of Object.entries(raw.Routes)) {
        const rs = routeSet as any;
        if (!rs.sonnet) {
          throw new Error(`Route set "${routeName}" must have a sonnet tier`);
        }
        config.Routes[routeName] = {
          sonnet: rs.sonnet,
          ...(rs.opus ? { opus: rs.opus } : {}),
          ...(rs.haiku ? { haiku: rs.haiku } : {}),
        };
      }

      if (Object.keys(config.Routes).length === 0) {
        throw new Error('Config must have at least one route set in Routes');
      }

      // Resolve active route
      const activeRouteName = activeRouteOverride || raw.ActiveRoute;
      if (!activeRouteName) {
        throw new Error('Config must have ActiveRoute (or use --route flag)');
      }
      if (!config.Routes[activeRouteName]) {
        const available = Object.keys(config.Routes).join(', ');
        throw new Error(`ActiveRoute "${activeRouteName}" not found in Routes. Available: ${available}`);
      }
      config.ActiveRoute = activeRouteName;
      config.Router = config.Routes[activeRouteName];
    } else if (raw.Router) {
      // Old format: single Router object (backward compat)
      const routerRaw = raw.Router;
      const sonnetEntry = routerRaw.sonnet || routerRaw.default;
      if (!sonnetEntry) {
        throw new Error('Config must have Router.sonnet (e.g., "anthropic,claude-sonnet-4-20250514")');
      }

      const routerConfig: RouterConfig = { sonnet: sonnetEntry };
      if (routerRaw.opus) routerConfig.opus = routerRaw.opus;
      if (routerRaw.haiku) routerConfig.haiku = routerRaw.haiku;

      config.Routes = { default: routerConfig };
      config.ActiveRoute = 'default';
      config.Router = routerConfig;
    } else {
      throw new Error('Config must have Routes (named route sets) or Router');
    }

    // --- Collect providers actually used by the active route ---
    const neededProviders = new Set<string>();
    for (const tier of ['sonnet', 'opus', 'haiku'] as const) {
      const entry = config.Router[tier];
      if (entry) {
        const comma = entry.indexOf(',');
        if (comma !== -1) {
          neededProviders.add(entry.substring(0, comma));
        }
      }
    }

    // --- Parse Providers (only those needed by the active route) ---
    // New format: { "anthropic": "$KEY", ... }
    // Old format: [{ name, api_base_url, api_key, models? }, ...]
    if (raw.Providers && !Array.isArray(raw.Providers) && typeof raw.Providers === 'object') {
      // New format: object { name: apiKey } or { name: { api_key, api_base_url? } }
      for (const [name, providerEntry] of Object.entries(raw.Providers)) {
        if (!neededProviders.has(name)) continue; // Skip providers not used by active route
        this.validateProviderName(name);
        const provider = name as SupportedProvider;
        const entry = providerEntry as any;
        // Support both string API key and { api_key, api_base_url? } object
        const apiKey = typeof entry === 'object' ? entry.api_key : entry;
        const baseUrl = typeof entry === 'object' && entry.api_base_url ? String(entry.api_base_url) : undefined;
        config.Providers.push({
          name: provider,
          api_base_url: baseUrl || PROVIDER_BASE_URLS[provider],
          api_key: this.interpolateEnvVar(apiKey as string),
        });
      }
    } else if (Array.isArray(raw.Providers) && raw.Providers.length > 0) {
      // Old format: array of provider objects (backward compat)
      for (const p of raw.Providers) {
        if (!neededProviders.has(p.name)) continue; // Skip providers not used by active route
        this.validateProviderLegacy(p);
        config.Providers.push({
          name: p.name as SupportedProvider,
          api_base_url: p.api_base_url || PROVIDER_BASE_URLS[p.name as SupportedProvider],
          api_key: this.interpolateEnvVar(p.api_key),
        });
      }
    } else {
      throw new Error('Config must have Providers (object or array)');
    }

    if (config.Providers.length === 0) {
      throw new Error('Config must have at least one provider');
    }

    // Validate all tier entries in the active route set
    this.validateRouterEntry('Router.sonnet', config.Router.sonnet, config.Providers);
    if (config.Router.opus) {
      this.validateRouterEntry('Router.opus', config.Router.opus, config.Providers);
    }
    if (config.Router.haiku) {
      this.validateRouterEntry('Router.haiku', config.Router.haiku, config.Providers);
    }

    // --- Parse Agents section for agent-based routing ---
    if (raw.Agents && typeof raw.Agents === 'object') {
      const agentsRaw = raw.Agents as any;
      config.Agents = {
        enable: agentsRaw.enable === true,
        agentsDir: agentsRaw.agentsDir || undefined,
        mappings: (agentsRaw.mappings && typeof agentsRaw.mappings === 'object')
          ? agentsRaw.mappings
          : {},
      };

      // Ensure agent target providers are loaded (so provider lookup succeeds later)
      for (const targetModel of Object.values(config.Agents.mappings) as string[]) {
        const provider = this.getProviderForModel(targetModel);
        if (!neededProviders.has(provider)) {
          // Add provider if not already included — will use default base URL + empty key
          const alreadyLoaded = config.Providers.some(p => p.name === provider);
          if (!alreadyLoaded) {
            this.validateProviderName(provider);
            config.Providers.push({
              name: provider as SupportedProvider,
              api_base_url: PROVIDER_BASE_URLS[provider as SupportedProvider],
              api_key: '',
            });
          }
          neededProviders.add(provider);
        }
      }
    }

    // Load agent definitions into subagents map (must happen after config.Providers is populated)
    if (config.Agents) {
      this.loadAgents(config.Agents);
    }

    return config;
  }

  private validateProviderName(name: string): void {
    if (!(SUPPORTED_PROVIDERS as readonly string[]).includes(name)) {
      throw new Error(
        `Invalid provider name "${name}". Must be one of: ${SUPPORTED_PROVIDERS.join(', ')}`,
      );
    }
  }

  private validateProviderLegacy(p: any): void {
    if (!p.name || !p.api_key) {
      throw new Error(`Provider missing required fields (name, api_key): ${JSON.stringify(p)}`);
    }
    this.validateProviderName(p.name);
  }

  private validateRouterEntry(field: string, value: string, providers: ProviderConfig[]): void {
    const comma = value.indexOf(',');
    if (comma === -1) {
      throw new Error(`${field} must be "providerName,modelName" format, got: "${value}"`);
    }
    const providerName = value.substring(0, comma);
    if (!providers.some((p) => p.name === providerName)) {
      throw new Error(`${field} references provider "${providerName}" which is not configured`);
    }
  }

  private interpolateEnvVar(value: string): string {
    return interpolateEnvVar(value);
  }

  get<K extends keyof AppConfig>(key: K): AppConfig[K] {
    return this.config[key];
  }

  getConfig(): AppConfig {
    return this.config;
  }

  getProvider(name: string): ProviderConfig | undefined {
    return this.config.Providers.find((p) => p.name === name);
  }

  getSubagents(): Map<string, SubagentDefinition> {
    return this.subagents;
  }

  isAgentsEnabled(): boolean {
    return this.config.Agents?.enable === true;
  }

  /** Extract the static portion of a system prompt (before "Notes:" section) */
  extractStaticPrompt(systemPrompt: string): string {
    let idx = systemPrompt.indexOf('\nNotes:');
    if (idx === -1) idx = systemPrompt.indexOf('\n\nNotes:');
    if (idx === -1) return systemPrompt.trim();
    return systemPrompt.substring(0, idx).trim();
  }

  /** SHA256 hash of prompt, first 16 hex chars */
  hashPrompt(prompt: string): string {
    return crypto.createHash('sha256').update(prompt).digest('hex').substring(0, 16);
  }

  /** Look up a subagent by the static portion of its system prompt.
   *  Returns the SubagentDefinition if found, undefined otherwise. */
  resolveAgent(staticPrompt: string): SubagentDefinition | undefined {
    const hash = this.hashPrompt(staticPrompt);
    return this.subagents.get(hash);
  }

  /** Parse a Router entry like "anthropic,claude-sonnet-4" into { provider, model } */
  parseRouterEntry(entry: string): { provider: string; model: string } {
    const comma = entry.indexOf(',');
    return {
      provider: entry.substring(0, comma),
      model: entry.substring(comma + 1),
    };
  }

  /** Classify an incoming model name into a tier based on substring matching */
  classifyModelTier(model: string): ModelTier {
    const lower = model.toLowerCase();
    for (const { tier, match } of MODEL_TIER_PATTERNS) {
      if (lower.includes(match)) return tier;
    }
    return 'sonnet'; // default fallback
  }

  /** Resolve an incoming model name to the configured provider and model for its tier */
  resolveModel(model: string): { provider: string; model: string } {
    const tier = this.classifyModelTier(model);
    const router = this.config.Router;
    const entry = router[tier] || router.sonnet;
    return this.parseRouterEntry(entry);
  }

  // ---------------------------------------------------------------------------
  // Agent-based routing
  // ---------------------------------------------------------------------------

  /** Determine provider name from model name prefix (mirrors old proxy logic) */
  private getProviderForModel(modelName: string): SupportedProvider {
    const lower = modelName.toLowerCase();
    if (lower.startsWith('gpt-') || lower.startsWith('o1') || lower.startsWith('o3')) return 'openai';
    if (lower.startsWith('glm-')) return 'glm';
    if (lower.startsWith('minimax-')) return 'minimax';
    if (lower.startsWith('gemini-')) return 'gemini';
    return 'anthropic';
  }

  /** Load agent definitions from markdown files and populate subagents map */
  private loadAgents(agentsConfig: AgentsConfig): void {
    if (!agentsConfig.enable) return;
    if (!agentsConfig.mappings || Object.keys(agentsConfig.mappings).length === 0) return;

    // Determine agent directory
    let agentsDir = agentsConfig.agentsDir || '';
    if (agentsDir && !require('path').isAbsolute(agentsDir)) {
      // Resolve relative paths against config file directory
      agentsDir = join(this.configPath ? require('path').dirname(this.configPath) : process.cwd(), agentsDir);
    }

    // Fallback default: ~/.claude/agents
    const defaultAgentsDir = join(CONFIG_DIR, 'agents');

    for (const [agentName, targetModel] of Object.entries(agentsConfig.mappings)) {
      const candidates = agentsDir
        ? [join(agentsDir, `${agentName}.md`), join(defaultAgentsDir, `${agentName}.md`)]
        : [join(defaultAgentsDir, `${agentName}.md`)];

      let found = false;
      for (const filePath of candidates) {
        if (!existsSync(filePath)) continue;

        try {
          const content = readFileSync(filePath, 'utf-8');
          const parts = content.split('\n---\n');
          if (parts.length < 2) continue;

          const systemPrompt = parts[1].trim();
          const staticPrompt = this.extractStaticPrompt(systemPrompt);
          const hash = this.hashPrompt(staticPrompt);
          const targetProvider = this.getProviderForModel(targetModel);

          this.subagents.set(hash, {
            name: agentName,
            targetProvider,
            targetModel,
            staticPrompt,
          });
          found = true;
          break;
        } catch {
          // File read error — try next candidate
        }
      }

      if (!found) {
        console.warn(`⚠️  Agent '${agentName}' mapped to '${targetModel}' but definition file not found`);
      }
    }
  }
}

export { CONFIG_DIR, CONFIG_FILE };
