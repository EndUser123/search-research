// MinimaxTransformer — Anthropic-compatible passthrough with x-api-key auth.
//
// MiniMax exposes an Anthropic-compatible endpoint at api.minimax.io/anthropic.
// This transformer injects the x-api-key header and passes requests through
// without transformation.

import type { Transformer, UnifiedChatRequest, ProviderConfig } from '../types';
import { createApiError } from '../api/middleware';

export class MinimaxTransformer implements Transformer {
  name = 'minimax';
  endPoint = '/anthropic';

  async auth(_request: Record<string, any>, provider: ProviderConfig) {
    const apiKey = provider.api_key;
    if (!apiKey || apiKey.trim() === '' || apiKey === '$MINIMAX_API_KEY') {
      throw createApiError(
        'MINIMAX_API_KEY environment variable is not set. Please configure your MiniMax API key.',
        500,
        'missing_api_key'
      );
    }

    return {
      body: _request,
      config: {
        headers: {
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
        } as Record<string, string>,
      },
    };
  }

  async transformRequestIn(request: UnifiedChatRequest, provider: ProviderConfig) {
    const body: Record<string, any> = { ...request };

    // Strip fields MiniMax doesn't support
    delete body.reasoning;

    // Strip cache_control from messages
    if (body.messages) {
      for (const msg of body.messages as Record<string, any>[]) {
        if (msg.cache_control) delete msg.cache_control;
        if (Array.isArray(msg.content)) {
          for (const item of msg.content as Record<string, any>[]) {
            if (item.cache_control) delete item.cache_control;
          }
        }
      }
    }

    // Set auth header: MiniMax Anthropic-compatible endpoint expects Authorization: Bearer
    const headers: Record<string, string> = {
      'anthropic-version': '2023-06-01',
    };
    if (provider.api_key) {
      headers['authorization'] = `Bearer ${provider.api_key}`;
    }

    // Set full URL with path - router uses config.url if present
    // Provider base is https://api.minimax.io/anthropic, we need /v1/messages appended
    const base = provider.api_base_url.replace(/\/$/, '');
    const url = new URL(`${base}/v1/messages`);

    return { body, config: { headers, url } };
  }

  // Transform MiniMax response to OpenAI/unified format.
  // MiniMax returns an almost-Anthropic-compatible response but includes:
  // - content[].type === "thinking" blocks (MiniMax-specific) — strip these
  // - content[].signature — strip
  // - base_resp field — strip
  // - stop_reason: "max_tokens" → "stop" (OpenAI convention)
  // Output must be OpenAI format so anthropicTransformer.transformResponseIn
  // can convert it to Anthropic format for Claude Code.
  async transformResponseOut(response: Response): Promise<Response> {
    const contentType = response.headers.get('Content-Type') || '';
    if (!contentType.includes('application/json')) {
      return response;
    }

    let data: any;
    try {
      data = await response.clone().json();
    } catch {
      return response;
    }

    // If it's an error response, normalize it to OpenAI error format
    if (data.error) {
      const error = data.error as Record<string, unknown>;
      return new Response(JSON.stringify({
        error: {
          message: (error.message as string) || String(error),
          type: (error.type as string) || 'provider_error',
          code: error.code as string | undefined,
        },
      }), {
        status: response.status,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Transform success response to OpenAI/unified format
    // Extract text content (strip thinking blocks and signatures)
    let textContent = '';
    if (Array.isArray(data.content)) {
      const textBlocks = data.content
        .filter((item: any) => item.type !== 'thinking' && item.type === 'text')
        .map((item: any) => item.text);
      textContent = textBlocks.join('\n');
    }

    // Map stop_reason to OpenAI convention
    const stopReason = data.stop_reason === 'max_tokens' ? 'length' : 'stop';

    // Build OpenAI-style response
    const openai: Record<string, any> = {
      id: data.id || `minimax-${Date.now()}`,
      model: data.model,
      choices: [{
        index: 0,
        message: {
          role: 'assistant',
          content: textContent,
        },
        finish_reason: stopReason,
      }],
    };

    // Map usage
    if (data.usage) {
      openai.usage = {
        prompt_tokens: data.usage.input_tokens ?? 0,
        completion_tokens: data.usage.output_tokens ?? 0,
        total_tokens: (data.usage.input_tokens ?? 0) + (data.usage.output_tokens ?? 0),
      };
    }

    return new Response(JSON.stringify(openai), {
      status: response.status,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
