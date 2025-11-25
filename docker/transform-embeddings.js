#!/usr/bin/env node
/**
 * 简单的 HTTP 中间件，用于转换 Blinko 的 embeddings 请求格式
 * 将 encoding_format 转换为 embedding_type
 */

const http = require('http');
const https = require('https');

const PORT = 9000;
const JINA_API_URL = 'https://api.jina.ai/v1/embeddings';
const JINA_API_KEY = process.env.JINA_API_KEY;

console.log('Starting embeddings transform middleware...');
console.log(`PORT: ${PORT}`);
console.log(`JINA_API_KEY: ${JINA_API_KEY ? 'set' : 'NOT SET'}`);

if (!JINA_API_KEY) {
  console.error('Error: JINA_API_KEY environment variable is not set');
  process.exit(1);
}

const server = http.createServer((req, res) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  console.log('Headers:', req.headers);

  if (req.method !== 'POST' || req.url !== '/v1/embeddings') {
    console.log('Invalid method or path');
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not found' }));
    return;
  }

  let body = '';
  req.on('data', chunk => {
    body += chunk.toString();
  });

  req.on('end', () => {
    try {
      console.log('Raw request body:', body);
      
      // 解析请求体
      const data = JSON.parse(body);
      console.log('Parsed request data:', JSON.stringify(data, null, 2));

      // 将 encoding_format 转换为 embedding_type
      if (data.encoding_format) {
        console.log(`Converting encoding_format: ${data.encoding_format} -> embedding_type`);
        data.embedding_type = data.encoding_format;
        delete data.encoding_format;
      }

      console.log('Modified request data:', JSON.stringify(data, null, 2));

      // 转发到 Jina API
      const options = {
        hostname: 'api.jina.ai',
        path: '/v1/embeddings',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${JINA_API_KEY}`,
          'Accept': 'application/json'
        }
      };

      console.log('Forwarding to Jina API with options:', JSON.stringify(options, null, 2));

      const proxyReq = https.request(options, (proxyRes) => {
        console.log(`Jina API response status: ${proxyRes.statusCode}`);
        console.log('Jina API response headers:', proxyRes.headers);

        let responseBody = '';
        proxyRes.on('data', chunk => {
          responseBody += chunk.toString();
        });

        proxyRes.on('end', () => {
          console.log('Jina API response body length:', responseBody.length);
          if (responseBody.length < 500) {
            console.log('Jina API response body:', responseBody);
          } else {
            console.log('Jina API response body (first 500 chars):', responseBody.substring(0, 500));
          }
          
          try {
            // 解析 Jina 的响应
            const jinaResponse = JSON.parse(responseBody);
            
            // 转换为 OpenAI 兼容格式
            const openaiResponse = {
              object: jinaResponse.object || 'list',
              data: jinaResponse.data || [],
              model: jinaResponse.model,
              usage: {
                prompt_tokens: jinaResponse.usage?.total_tokens || 0,
                total_tokens: jinaResponse.usage?.total_tokens || 0
              }
            };
            
            console.log('Converted to OpenAI format');
            const convertedBody = JSON.stringify(openaiResponse);
            console.log('Converted response body length:', convertedBody.length);
            
            // 更新响应头中的 content-length
            const responseHeaders = { ...proxyRes.headers };
            responseHeaders['content-length'] = Buffer.byteLength(convertedBody);
            
            res.writeHead(proxyRes.statusCode, responseHeaders);
            res.end(convertedBody);
          } catch (error) {
            console.error('Error converting response format:', error);
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Response conversion failed', details: error.message }));
          }
        });
      });

      proxyReq.on('error', (error) => {
        console.error('Error forwarding to Jina API:', error);
        res.writeHead(502, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Bad Gateway', details: error.message }));
      });

      const requestBody = JSON.stringify(data);
      console.log('Sending to Jina API:', requestBody);
      proxyReq.write(requestBody);
      proxyReq.end();
    } catch (error) {
      console.error('Error processing request:', error);
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Bad Request', details: error.message }));
    }
  });
});

server.listen(PORT, () => {
  console.log(`Transform middleware listening on port ${PORT}`);
  console.log(`Forwarding /v1/embeddings to ${JINA_API_URL}`);
});
