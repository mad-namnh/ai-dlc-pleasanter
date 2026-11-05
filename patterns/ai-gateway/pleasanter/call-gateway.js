// Replacement for apiKey() + callClaude() in an AI server script (e.g. "AI問い合わせ一次対応").
// - No API key in Pleasanter anymore. Calls the internal AI gateway; the gateway calls Bedrock with an IAM role.
// - CONF.model is now a gateway ALIAS (e.g. 'fast'), not a model id.
// - CONF.effort is no longer used (Bedrock Converse does not accept it).
// - Same signature: callClaude(prompt) → parsed JSON object, so the rest of the script is unchanged.
// User-facing messages stay in Japanese (they are shown to Pleasanter users).

function gatewayUrl() {
    if (typeof AI_GATEWAY_URL === 'undefined' || !AI_GATEWAY_URL || AI_GATEWAY_URL.indexOf('${') === 0) {
        throw new Error('AI_GATEWAY_URL が設定されていません（共有スクリプト「共通設定（環境）」を確認）');
    }
    return AI_GATEWAY_URL.replace(/\/+$/, '');
}

function callClaude(prompt) {
    httpClient.RequestUri = gatewayUrl() + '/v1/generate';
    httpClient.RequestHeaders.Clear();
    httpClient.TimeOut = CONF.timeoutMs;
    httpClient.Content = JSON.stringify({
        model: CONF.model,
        system: CONF.system,
        prompt: prompt,
        max_tokens: CONF.maxTokens,
        caller: {
            site_id: (typeof context !== 'undefined' && context.SiteId) ? context.SiteId : null,
            record_id: model.ResultId || model.IssueId || null,
            feature: CONF.title
        }
    });
    const text = httpClient.Post();
    if (httpClient.IsTimeOut) throw new Error('AIの応答がタイムアウトしました');
    let res = null;
    try { res = JSON.parse(text); } catch (e) { /* body is not JSON */ }
    if (!httpClient.IsSuccess) {
        const code = res && res.error ? res.error.code : '';
        const reasons = {
            upstream_throttled: 'AIの利用が混み合っています。時間をおいて再実行してください',
            upstream_timeout: 'AIの応答がタイムアウトしました',
            upstream_unavailable: 'AIのサーバが混み合っています。時間をおいて再実行してください',
            upstream_access_denied: 'AIゲートウェイにモデルの利用権限がありません',
            unknown_model: 'AIのモデル設定が正しくありません',
            prompt_too_large: '入力が長すぎます'
        };
        throw new Error(`${reasons[code] || 'AIゲートウェイでエラーが発生しました'}（HTTP ${httpClient.StatusCode}${code ? ' ' + code : ''}）`);
    }
    if (!res || typeof res.text !== 'string' || !res.text) throw new Error('AIの応答に本文がありません');
    // Strip anything around the JSON object (code fences, etc.) before parsing
    const raw = res.text;
    return JSON.parse(raw.slice(raw.indexOf('{'), raw.lastIndexOf('}') + 1));
}
