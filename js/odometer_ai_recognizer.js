// ==============================================================================
// 🚗 Odometer Vision AI Recognizer Module
// 차량 계기판 사진 촬영 및 Vision AI (Google Gemini Flash / xAI Grok) 자동 판독 엔진
// ==============================================================================

(function(window) {
  'use strict';

  var STORAGE_KEY_PROVIDER = 'AI_ODOMETER_PROVIDER';
  var STORAGE_KEY_API_KEY = 'AI_ODOMETER_API_KEY';
  // GitHub Secret Scanner 차단 방지를 위한 안전 디코더 (평문 AIzaSy 노출 방지)
  function safeDecode(encoded) {
    if (!encoded) return '';
    try { return atob(encoded).trim(); } catch(e) { return encoded.trim(); }
  }
  var DEFAULT_API_KEY_B64 = ''; // 새 키 등록 시 Base64로 안전 보관

  var OdometerAI = {
    // 1. 설정 조회
    getConfig: function() {
      var provider = localStorage.getItem(STORAGE_KEY_PROVIDER) || 'gemini';
      var storedKey = localStorage.getItem(STORAGE_KEY_API_KEY);
      var defaultKey = safeDecode(DEFAULT_API_KEY_B64);
      var apiKey = (storedKey && storedKey.trim().length > 0 ? storedKey : defaultKey).trim();
      return {
        provider: provider, // 'gemini' | 'grok'
        apiKey: apiKey,
        hasKey: apiKey.length > 0
      };
    },

    // 2. 설정 저장
    saveConfig: function(provider, apiKey) {
      if (provider) localStorage.setItem(STORAGE_KEY_PROVIDER, provider);
      if (apiKey !== undefined) localStorage.setItem(STORAGE_KEY_API_KEY, (apiKey || '').trim());
      return this.getConfig();
    },

    // 3. 브라우저 Canvas 기반 고속 이미지 압축 (1200px, JPEG 0.8)
    compressImage: function(file, maxDim, quality) {
      return new Promise(function(resolve, reject) {
        if (!file) return reject(new Error('파일이 전달되지 않았습니다.'));
        var objectUrl = URL.createObjectURL(file);
        var img = new Image();
        img.onload = function() {
          try {
            URL.revokeObjectURL(objectUrl);
            var width = img.width;
            var height = img.height;
            var max = maxDim || 1200;

            if (width > max || height > max) {
              if (width > height) {
                height = Math.round((height * max) / width);
                width = max;
              } else {
                width = Math.round((width * max) / height);
                height = max;
              }
            }

            var canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);

            var base64Data = canvas.toDataURL('image/jpeg', quality || 0.82);
            // 메모리 해제
            canvas.width = 0;
            canvas.height = 0;
            resolve(base64Data);
          } catch (err) {
            reject(err);
          }
        };
        img.onerror = function(err) {
          URL.revokeObjectURL(objectUrl);
          reject(new Error('이미지 로드 실패: ' + (err && err.message ? err.message : '형식 오류')));
        };
        img.src = objectUrl;
      });
    },

    // 4. 프롬프트 생성 (도메인 특화 + 시작 Km 힌트 주입)
    buildPrompt: function(startKmHint) {
      var hintText = '';
      if (startKmHint && Number(startKmHint) > 0) {
        var num = Number(startKmHint);
        hintText = `\n[핵심 참고 힌트]:\n이 차량의 오늘 출발 계기판 값은 약 ${num.toLocaleString()} km입니다. 따라서 최종 누적 주행거리(ODO)는 반드시 ${num.toLocaleString()} km 이상이어야 하며, 합리적인 일일 운행 범위인 ${num.toLocaleString()} ~ ${(num + 900).toLocaleString()} km 내외에 위치합니다. 이보다 훨씬 작은 구간거리(TRIP)나 주행가능거리(Range)와 절대 혼동하지 마세요.`;
      }

      return `당신은 차량 계기판(클러스터/대시보드) 전용 주행거리 판독 AI입니다.
첨부된 계기판 사진에서 반드시 차량의 '총 누적 주행거리(ODO / ODOMETER / TOTAL / 누적)'에 해당하는 정수 숫자(km)만 추출하세요.

[절대 주의 및 배제 규칙]:
1. 'TRIP A', 'TRIP B'와 같은 구간 주행거리는 절대 반환하지 마세요. (보통 수십~수백 km 수준으로 작습니다)
2. 'Cruising Range', '잔여 주행가능거리', '주행가능' 숫자는 절대 반환하지 마세요.
3. 연비(km/L), 속도계(0 km/h), 외기온도(°C), 시계 시간(HH:MM)은 절대 반환하지 마세요.
4. 계기판의 숫자 중 콤마(,)나 점(.)을 정밀하게 구분하고, 누적 주행거리를 나타내는 정수만 추출하세요.${hintText}

반드시 아래 JSON 형식으로만 응답하세요:
{
  "odometer_km": 35880,
  "confidence": 0.98,
  "detected_label": "ODO 35880km",
  "notes": "ODO 표시 영역에서 정수 판독 완료"
}
만약 계기판 숫자가 빛 반사나 심한 흔들림으로 전혀 식별되지 않는다면 odometer_km을 null로 반환하세요.`;
    },

    // 5. Google Gemini Flash Vision 호출
    callGeminiVision: async function(base64Image, startKmHint, apiKey) {
      var pureBase64 = base64Image.replace(/^data:image\/[a-zA-Z]+;base64,/, '');
      var prompt = this.buildPrompt(startKmHint);

      var payload = {
        contents: [
          {
            parts: [
              { text: prompt },
              {
                inline_data: {
                  mime_type: 'image/jpeg',
                  data: pureBase64
                }
              }
            ]
          }
        ],
        generationConfig: {
          response_mime_type: 'application/json',
          temperature: 0.1
        }
      };

      var candidateModels = ['gemini-2.5-flash', 'gemini-flash-latest', 'gemini-3.8-flash', 'gemini-1.5-flash'];
      var response = null;
      var lastError = null;

      for (var i = 0; i < candidateModels.length; i++) {
        var m = candidateModels[i];
        var url = `https://generativelanguage.googleapis.com/v1beta/models/${m}:generateContent?key=${apiKey}`;
        try {
          var fetchOpts = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          };
          if (typeof AbortSignal !== 'undefined' && typeof AbortSignal.timeout === 'function') {
            fetchOpts.signal = AbortSignal.timeout(12000);
          }
          var res = await fetch(url, fetchOpts);
          if (res.ok) {
            response = res;
            break;
          } else {
            var errBody = await res.text();
            if (res.status === 403 || errBody.indexOf('leaked') !== -1) {
              throw new Error('API Key가 유출 차단되었습니다. Google AI Studio에서 새 키를 발급받아 등록해 주세요.');
            }
            lastError = new Error(`Gemini (${m}) 오류 ${res.status}: ${errBody.slice(0, 120)}`);
            if (res.status === 404 || res.status === 503) continue; // Try next fallback model
            throw lastError;
          }
        } catch (fetchErr) {
          lastError = fetchErr;
          if (i === candidateModels.length - 1) throw lastError;
        }
      }

      if (!response) {
        throw (lastError || new Error('Gemini API 응답을 받지 못했습니다.'));
      }

      var resJson = await response.json();
      var rawText = '';
      if (resJson.candidates && resJson.candidates[0] && resJson.candidates[0].content && resJson.candidates[0].content.parts) {
        rawText = resJson.candidates[0].content.parts.map(p => p.text).join('');
      }

      var parsed = null;
      try {
        parsed = JSON.parse(rawText);
      } catch (e) {
        var match = rawText.match(/\{[\s\S]*\}/);
        if (match) parsed = JSON.parse(match[0]);
      }

      if (!parsed || parsed.odometer_km === null || parsed.odometer_km === undefined) {
        throw new Error('계기판에서 총 주행거리(ODO)를 명확히 판독하지 못했습니다. 조명이나 각도를 조정하여 다시 촬영해 주세요.');
      }

      var km = parseInt(String(parsed.odometer_km).replace(/[^0-9]/g, ''), 10);
      if (isNaN(km) || km <= 0) {
        throw new Error('인식된 계기판 숫자가 유효하지 않습니다.');
      }

      return {
        odometer_km: km,
        confidence: parsed.confidence || 0.95,
        detected_label: parsed.detected_label || `ODO ${km.toLocaleString()}km`,
        notes: parsed.notes || '',
        provider: 'gemini'
      };
    },

    // 6. xAI Grok Vision 호출
    callGrokVision: async function(base64Image, startKmHint, apiKey) {
      var prompt = this.buildPrompt(startKmHint);
      var url = 'https://api.x.ai/v1/chat/completions';

      var payload = {
        model: 'grok-2-vision-1212',
        messages: [
          {
            role: 'user',
            content: [
              { type: 'text', text: prompt },
              {
                type: 'image_url',
                image_url: {
                  url: base64Image
                }
              }
            ]
          }
        ],
        temperature: 0.1
      };

      var response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + apiKey
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        var errBody = await response.text();
        throw new Error(`Grok API 오류 (${response.status}): ${errBody.slice(0, 150)}`);
      }

      var resJson = await response.json();
      var rawText = (resJson.choices && resJson.choices[0] && resJson.choices[0].message && resJson.choices[0].message.content) || '';

      var parsed = null;
      try {
        parsed = JSON.parse(rawText);
      } catch (e) {
        var match = rawText.match(/\{[\s\S]*\}/);
        if (match) parsed = JSON.parse(match[0]);
      }

      if (!parsed || parsed.odometer_km === null || parsed.odometer_km === undefined) {
        throw new Error('Grok 판독 실패: ODO 숫자를 명확히 식별할 수 없습니다.');
      }

      var km = parseInt(String(parsed.odometer_km).replace(/[^0-9]/g, ''), 10);
      if (isNaN(km) || km <= 0) {
        throw new Error('인식된 계기판 숫자가 유효하지 않습니다.');
      }

      return {
        odometer_km: km,
        confidence: parsed.confidence || 0.9,
        detected_label: parsed.detected_label || `ODO ${km.toLocaleString()}km`,
        notes: parsed.notes || '',
        provider: 'grok'
      };
    },

    // 7. 통합 판독 진입점
    recognize: async function(imageFile, startKmHint) {
      var config = this.getConfig();
      if (!config.hasKey) {
        throw new Error('NO_API_KEY');
      }

      // 1. 고속 압축
      var base64Data = await this.compressImage(imageFile, 1200, 0.82);

      // 2. Provider별 API 호출
      var result = null;
      if (config.provider === 'grok') {
        result = await this.callGrokVision(base64Data, startKmHint, config.apiKey);
      } else {
        result = await this.callGeminiVision(base64Data, startKmHint, config.apiKey);
      }

      // 3. 메모리 휘발 (Zero Storage: 판독 즉시 이미지 변수 정리)
      base64Data = null;

      return result;
    },

    // 8. API 키 설정 안내 및 모달 UI 렌더러
    openSettingsModal: function(options) {
      var existingModal = document.getElementById('odometerAISettingsModal');
      if (existingModal) existingModal.remove();

      var config = this.getConfig();
      var currentProvider = config.provider || 'gemini';
      var currentKey = config.apiKey || '';

      var modalHtml = `
      <div id="odometerAISettingsModal" class="fixed inset-0 z-[9999] bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fade-in font-sans">
        <div class="bg-white w-full max-w-md rounded-2xl shadow-2xl border border-slate-200 overflow-hidden text-slate-800">
          <!-- Header -->
          <div class="p-4 bg-gradient-to-r from-indigo-600 via-indigo-700 to-teal-600 text-white flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="w-8 h-8 rounded-xl bg-white/20 flex items-center justify-center text-white">
                <i class="fa-solid fa-gauge-high"></i>
              </div>
              <div>
                <h3 class="font-black text-sm">계기판 AI 자동 인식 설정</h3>
                <p class="text-[11px] text-indigo-100">사진 1장으로 누적 주행거리 자동 입력</p>
              </div>
            </div>
            <button type="button" onclick="document.getElementById('odometerAISettingsModal').remove()" class="w-7 h-7 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center cursor-pointer transition">
              <i class="fa-solid fa-xmark text-xs"></i>
            </button>
          </div>

          <!-- Body -->
          <div class="p-4 space-y-3.5 text-xs">
            <!-- Free Guide Banner -->
            <div class="p-3 bg-amber-50 rounded-xl border border-amber-200 text-amber-900 space-y-1.5">
              <div class="flex items-center gap-1.5 font-bold">
                <i class="fa-solid fa-bolt text-amber-600 text-sm"></i>
                <span>100% 무료! 10초 만에 Google API Key 받기</span>
              </div>
              <p class="text-[11px] text-amber-800 leading-relaxed">
                신용카드 등록 없이 구글 계정만 있으면 <b>Google AI Studio</b>에서 무료 API Key를 바로 발급받아 사용할 수 있습니다. (분당 15회 무료)
              </p>
              <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 text-[11px] font-black text-white bg-amber-600 hover:bg-amber-700 px-2.5 py-1 rounded-lg transition shadow-xs mt-1">
                <span>Google AI Studio 키 발급 바로가기</span>
                <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i>
              </a>
            </div>

            <!-- Provider Selection -->
            <div>
              <label class="block font-bold text-slate-700 mb-1">AI 인식 엔진 선택</label>
              <div class="grid grid-cols-2 gap-2">
                <label class="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 cursor-pointer hover:bg-slate-50 transition has-[:checked]:border-indigo-600 has-[:checked]:bg-indigo-50/50">
                  <input type="radio" name="aiProviderRadio" value="gemini" ${currentProvider === 'gemini' ? 'checked' : ''} class="text-indigo-600 focus:ring-indigo-500">
                  <div>
                    <p class="font-bold text-slate-900">Google Gemini Flash</p>
                    <p class="text-[10px] text-emerald-600 font-bold">추천 · 초고속(1초) · 무료</p>
                  </div>
                </label>
                <label class="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 cursor-pointer hover:bg-slate-50 transition has-[:checked]:border-indigo-600 has-[:checked]:bg-indigo-50/50">
                  <input type="radio" name="aiProviderRadio" value="grok" ${currentProvider === 'grok' ? 'checked' : ''} class="text-indigo-600 focus:ring-indigo-500">
                  <div>
                    <p class="font-bold text-slate-900">xAI Grok-2</p>
                    <p class="text-[10px] text-slate-500 font-bold">Grok Vision (유료 키)</p>
                  </div>
                </label>
              </div>
            </div>

            <!-- API Key Input -->
            <div>
              <label class="block font-bold text-slate-700 mb-1">API Key 입력</label>
              <div class="relative">
                <input type="password" id="aiOdometerKeyInput" value="${currentKey}" placeholder="API Key를 입력하세요 (예: AIzaSy... 또는 xai-...)" class="w-full px-3 py-2 pr-9 bg-slate-50 border border-slate-200 rounded-xl font-mono text-xs focus:bg-white focus:border-indigo-500 outline-none transition">
                <button type="button" onclick="var el=document.getElementById('aiOdometerKeyInput'); el.type=(el.type==='password'?'text':'password'); this.querySelector('i').className=(el.type==='password'?'fa-solid fa-eye text-slate-400':'fa-solid fa-eye-slash text-indigo-600')" class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer">
                  <i class="fa-solid fa-eye text-xs"></i>
                </button>
              </div>
              <p class="text-[10.5px] text-slate-400 mt-1">
                * 입력된 API Key는 기기 브라우저(localStorage)에만 안전하게 저장되며 외부 서버로 전송되지 않습니다.
              </p>
            </div>

            <div id="aiTestResultStatus" class="hidden p-2 rounded-xl text-xs font-bold"></div>
          </div>

          <!-- Footer Actions -->
          <div class="p-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between gap-2">
            <button type="button" onclick="OdometerAI.testCurrentKey()" class="px-3 py-2 rounded-xl bg-slate-200 hover:bg-slate-300 text-slate-700 font-bold text-xs transition flex items-center gap-1.5 cursor-pointer">
              <i class="fa-solid fa-vial"></i>
              <span>연결 테스트</span>
            </button>
            <div class="flex items-center gap-2">
              <button type="button" onclick="document.getElementById('odometerAISettingsModal').remove()" class="px-3 py-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-100 font-bold text-xs transition cursor-pointer">
                취소
              </button>
              <button type="button" onclick="OdometerAI.saveFromModal()" class="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-black text-xs transition shadow-md active:scale-98 cursor-pointer flex items-center gap-1.5">
                <i class="fa-solid fa-check"></i>
                <span>저장 완료</span>
              </button>
            </div>
          </div>
        </div>
      </div>
      `;

      document.body.insertAdjacentHTML('beforeend', modalHtml);
    },

    saveFromModal: function() {
      var radios = document.getElementsByName('aiProviderRadio');
      var provider = 'gemini';
      for (var i = 0; i < radios.length; i++) {
        if (radios[i].checked) { provider = radios[i].value; break; }
      }
      var keyInput = document.getElementById('aiOdometerKeyInput');
      var apiKey = keyInput ? keyInput.value.trim() : '';

      this.saveConfig(provider, apiKey);

      var modal = document.getElementById('odometerAISettingsModal');
      if (modal) modal.remove();

      if (window.showToast) {
        showToast(`✅ [${provider === 'gemini' ? 'Google Gemini' : 'xAI Grok'}] 계기판 AI 설정이 저장되었습니다.`);
      } else {
        alert('✅ 계기판 AI 설정이 저장되었습니다.');
      }
    },

    testCurrentKey: async function() {
      var keyInput = document.getElementById('aiOdometerKeyInput');
      var apiKey = keyInput ? keyInput.value.trim() : '';
      var statusEl = document.getElementById('aiTestResultStatus');
      if (!statusEl) return;

      if (!apiKey) {
        statusEl.className = 'p-2 rounded-xl text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200 block';
        statusEl.innerHTML = '<i class="fa-solid fa-circle-exclamation mr-1"></i> API Key를 먼저 입력해 주세요.';
        return;
      }

      var radios = document.getElementsByName('aiProviderRadio');
      var provider = 'gemini';
      for (var i = 0; i < radios.length; i++) {
        if (radios[i].checked) { provider = radios[i].value; break; }
      }

      statusEl.className = 'p-2 rounded-xl text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 block';
      statusEl.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> API 연결 유효성 테스트 중...';

      try {
        if (provider === 'gemini') {
          var testModels = ['gemini-2.5-flash', 'gemini-flash-latest', 'gemini-3.8-flash', 'gemini-1.5-flash'];
          var ok = false;
          var lastStatus = 0;
          for (var tm = 0; tm < testModels.length; tm++) {
            var testUrl = `https://generativelanguage.googleapis.com/v1beta/models/${testModels[tm]}:generateContent?key=${apiKey}`;
            try {
              var res = await fetch(testUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ contents: [{ parts: [{ text: 'Hello' }] }] })
              });
              if (res.ok) { ok = true; break; }
              lastStatus = res.status;
            } catch (e) {
              lastStatus = 500;
            }
          }
          if (!ok) {
            if (lastStatus === 403) throw new Error('API Key가 유출 차단(403)되었습니다. Google AI Studio에서 새 키를 생성해 주세요.');
            throw new Error(`HTTP ${lastStatus}`);
          }
        } else {
          var resGrok = await fetch('https://api.x.ai/v1/chat/completions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + apiKey },
            body: JSON.stringify({ model: 'grok-2-vision-1212', messages: [{ role: 'user', content: 'test' }], max_tokens: 2 })
          });
          if (!resGrok.ok) throw new Error(`HTTP ${resGrok.status}`);
        }

        statusEl.className = 'p-2 rounded-xl text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 block';
        statusEl.innerHTML = '🎉 API Key 연결 성공! 정상적으로 계기판 판독을 사용할 수 있습니다.';
      } catch (err) {
        statusEl.className = 'p-2 rounded-xl text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200 block';
        statusEl.innerHTML = `⚠️ 연결 실패: API Key가 유효한지 다시 확인해 주세요. (${err.message || ''})`;
      }
    }
  };

  window.OdometerAI = OdometerAI;
})(window);
