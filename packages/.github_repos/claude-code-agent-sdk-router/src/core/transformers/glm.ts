// GlmTransformer — Anthropic-compatible passthrough with x-api-key auth.
//
// GLM's endpoint (api.z.ai/api/anthropic) is hypothesized to be Anthropic-compatible.
// This transformer injects the x-api-key header and passes requests through.
// A defensive transformResponseOut is included to normalize non-Anthropic error formats.

import type { Transformer, UnifiedChatRequest, ProviderConfig } from '../types';
import { createApiError } from '../api/middleware';

export class GlmTransformer implements Transformer {
  name = 'glm';
  endPoint = '/api/anthropic';

  async auth(_request: Record<string, any>, provider: ProviderConfig) {
    const apiKey = provider.api_key;
    if (!apiKey || apiKey.trim() === '' || apiKey === '$ZHIPU_API_KEY') {
      throw createApiError(
        'ZHIPU_API_KEY environment variable is not set. Please configure your GLM/Zhipu API key.',
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

  async transformRequestIn(request: UnifiedChatRequest, _provider: ProviderConfig) {
    const body: Record<string, any> = { ...request };

    // Strip fields GLM doesn't support
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

    return { body, config: { headers: {} } };
  }

  // Defensive error normalizer — GLM may return non-Anthropic error formats.
  // This transforms known GLM error shapes into Anthropic-compatible errors.
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

    // Check if this is an error that needs normalization
    if (!data.error) {
      return response;
    }

    const error = data.error as Record<string, unknown>;

    // GLM error format: { error: { message: "...", code: "..." } }
    // Anthropic error format: { error: { type: "...", message: "...", code: "..." } }
    const anthropicError = {
      error: {
        type: (error.type as string) || (error.code as string) || 'provider_error',
        message: (error.message as string) || String(error),
        code: error.code as string | undefined,
      },
    };

    return new Response(JSON.stringify(anthropicError), {
      status: response.status,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
