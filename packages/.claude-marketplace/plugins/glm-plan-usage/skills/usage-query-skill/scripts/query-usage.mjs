#!/usr/bin/env node

/**
 * Usage query script (local fork).
 *
 * Upstream reads ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN, but under cc-ccr those
 * point at the local CCR proxy (localhost:3456) + the proxy's key, so the upstream
 * URL validation rejects them. This fork ignores the proxy env entirely: it reads
 * ZAI_API_KEY (from process env, falling back to P:/.env) and targets api.z.ai
 * directly.
 */

import https from 'https';
import fs from 'fs';

function resolveZaiToken() {
  if (process.env.ZAI_API_KEY) return process.env.ZAI_API_KEY;
  try {
    const txt = fs.readFileSync('P:/.env', 'utf8');
    const m = txt.match(/^ZAI_API_KEY\s*=\s*"?(.*?)"?\s*$/m);
    if (m && m[1]) return m[1];
  } catch (_) { /* P:/.env not readable from this CWD — fall through */ }
  if (process.env.ANTHROPIC_AUTH_TOKEN) return process.env.ANTHROPIC_AUTH_TOKEN;
  console.error('Error: ZAI_API_KEY not found in process env or P:/.env');
  process.exit(1);
}

const authToken = resolveZaiToken();

const platform = 'ZAI';
const baseDomain = 'https://api.z.ai';
const modelUsageUrl = `${baseDomain}/api/monitor/usage/model-usage`;
const toolUsageUrl = `${baseDomain}/api/monitor/usage/tool-usage`;
const quotaLimitUrl = `${baseDomain}/api/monitor/usage/quota/limit`;

console.log(`Platform: ${platform}`);
console.log('');
// Time window: from yesterday at the current hour (HH:00:00) to today at the current hour end (HH:59:59).
const now = new Date();
const startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1, now.getHours(), 0, 0, 0);
const endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours(), 59, 59, 999);

// Format dates as yyyy-MM-dd HH:mm:ss
const formatDateTime = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
};

const startTime = formatDateTime(startDate);
const endtime = formatDateTime(endDate);

// Properly encode query parameters
const queryParams = `?startTime=${encodeURIComponent(startTime)}&endTime=${encodeURIComponent(endtime)}`;

const processQuotaLimit = (data) => {
  if (!data || !data.limits) return data;

  data.limits = data.limits.map(item => {
    if (item.type === 'TOKENS_LIMIT') {
      return {
        type: 'Token usage(5 Hour)',
        percentage: item.percentage
      };
    }
    if (item.type === 'TIME_LIMIT') {
      return {
        type: 'MCP usage(1 Month)',
        percentage: item.percentage,
        currentUsage: item.currentValue,
        totol: item.usage,
        usageDetails: item.usageDetails
      };
    }
    return item;
  });
  return data;
};

const queryUsage = (apiUrl, label, appendQueryParams = true, postProcessor = null) => {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(apiUrl);
    const options = {
      hostname: parsedUrl.hostname,
      port: 443,
      path: parsedUrl.pathname + (appendQueryParams ? queryParams : ''),
      method: 'GET',
      headers: {
        'Authorization': authToken,
        'Accept-Language': 'en-US,en',
        'Content-Type': 'application/json'
      }
    };

    const req = https.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        if (res.statusCode !== 200) {
          return reject(new Error(`[${label}] HTTP ${res.statusCode}\n${data}`));
        }

        console.log(`${label} data:`);
        console.log('');

        try {
          const json = JSON.parse(data);
          let outputData = json.data || json;
          if (postProcessor && json.data) {
            outputData = postProcessor(json.data);
          }
          console.log(JSON.stringify(outputData));
        } catch (e) {
          console.log('Response body:');
          console.log(data);
        }

        console.log('');
        resolve();
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.end();
  });
};

const run = async () => {
  await queryUsage(modelUsageUrl, 'Model usage');
  await queryUsage(toolUsageUrl, 'Tool usage');
  await queryUsage(quotaLimitUrl, 'Quota limit', false, processQuotaLimit);
};

run().catch((error) => {
  console.error('Request failed:', error.message);
  process.exit(1);
});
