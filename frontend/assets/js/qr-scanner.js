/**
 * assets/js/qr-scanner.js
 * Scanner QR local no navegador, com troca de câmera e fechamento confiável.
 */
const QRScanner = (() => {
  const CAPTURE_INTERVAL_MS = 700;
  const READ_COOLDOWN_MS = 1800;

  let _stream = null;
  let _timer = null;
  let _container = null;
  let _callback = null;
  let _inputId = null;
  let _preferredCameraId = null;
  let _availableCameras = [];
  let _switching = false;
  let _decoding = false;
  let _retryAt = 0;
  let _barcodeDetector = null;
  let _escHandler = null;
  let _videoEl = null;
  let _canvasEl = null;
  let _statusEl = null;
  let _selectEl = null;
  let _cancelBtnEl = null;
  let _refreshBtnEl = null;
  let _lastDecodedValue = "";
  let _lastReadAt = 0;

  function _getBarcodeDetector() {
    if (_barcodeDetector !== null) return _barcodeDetector;
    if (!window.BarcodeDetector) {
      _barcodeDetector = false;
      return _barcodeDetector;
    }

    try {
      _barcodeDetector = new window.BarcodeDetector({
        formats: ["qr_code", "code_128", "ean_13", "ean_8", "upc_a", "upc_e"],
      });
    } catch {
      _barcodeDetector = false;
    }

    return _barcodeDetector;
  }

  function _buildUI() {
    const root = document.createElement("div");
    root.id = "cam-container";
    root.innerHTML = `
      <h3><i class="ti ti-scan"></i> Aponte para o código</h3>
      <div class="cam-toolbar">
        <label for="cam-device-select">Câmera</label>
        <select id="cam-device-select"></select>
        <button class="cam-switch-btn" type="button" title="Trocar câmera">
          <span class="cam-switch-icon"><i class="ti ti-switch-vertical"></i></span>
          <span>Trocar câmera</span>
        </button>
      </div>
      <div class="cam-viewport">
        <video id="cam-video" autoplay playsinline muted></video>
        <canvas id="cam-canvas" style="display:none;"></canvas>
        <div class="cam-reticle"></div>
      </div>
      <p class="cam-status">Inicializando câmera...</p>
      <button class="btn btn-danger cam-cancel-btn" type="button">
        <i class="ti ti-x"></i> Cancelar
      </button>`;

    document.body.appendChild(root);
    _container = root;
    _selectEl = root.querySelector("#cam-device-select");
    _refreshBtnEl = root.querySelector(".cam-switch-btn");
    _videoEl = root.querySelector("#cam-video");
    _canvasEl = root.querySelector("#cam-canvas");
    _statusEl = root.querySelector(".cam-status");
    _cancelBtnEl = root.querySelector(".cam-cancel-btn");

    _cancelBtnEl?.addEventListener("click", stop);
    _refreshBtnEl?.addEventListener("click", () => refreshCameras());
    _selectEl?.addEventListener("change", async (event) => {
      const deviceId = event.target.value || null;
      if (!deviceId || deviceId === _preferredCameraId) return;
      await switchCamera(deviceId);
    });

    return root;
  }

  async function _enumerateCameras() {
    if (!navigator.mediaDevices?.enumerateDevices) return [];
    const devices = await navigator.mediaDevices.enumerateDevices();
    return devices.filter((device) => device.kind === "videoinput");
  }

  function _fillCameraSelect() {
    const select = _selectEl;
    if (!select) return;

    select.innerHTML = "";

    if (!_availableCameras.length) {
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "Nenhuma câmera disponível";
      select.appendChild(option);
      select.disabled = true;
      return;
    }

    select.disabled = false;
    _availableCameras.forEach((camera, index) => {
      const option = document.createElement("option");
      option.value = camera.deviceId;
      option.textContent = camera.label || `Câmera ${index + 1}`;
      if (camera.deviceId === _preferredCameraId) option.selected = true;
      select.appendChild(option);
    });
  }

  async function refreshCameras() {
    try {
      _availableCameras = await _enumerateCameras();
      _fillCameraSelect();
      return _availableCameras;
    } catch (error) {
      console.error("Erro ao listar câmeras:", error);
      return [];
    }
  }

  async function _startStream(constraints) {
    _stream = await navigator.mediaDevices.getUserMedia(constraints);
    if (_videoEl) {
      _videoEl.style.transform = "none";
      _videoEl.style.webkitTransform = "none";
      _videoEl.style.filter = "none";
      _videoEl.srcObject = _stream;
      await _videoEl.play();
    }
  }

  async function _startWithPreferredCamera() {
    const candidates = [];

    if (_preferredCameraId) {
      candidates.push({ video: { deviceId: { exact: _preferredCameraId } } });
    }

    candidates.push(
      { video: { facingMode: { ideal: "environment" } } },
      { video: { facingMode: { ideal: "user" } } },
      { video: true },
    );

    let lastError = null;
    for (const constraints of candidates) {
      try {
        await _startStream(constraints);
        return;
      } catch (error) {
        lastError = error;
      }
    }

    throw lastError || new Error("Câmera indisponível");
  }

  async function switchCamera(deviceId) {
    if (_switching) return;
    _switching = true;
    try {
      _preferredCameraId = deviceId;
      clearInterval(_timer);
      _timer = null;
      if (_stream) {
        _stream.getTracks().forEach((track) => track.stop());
        _stream = null;
      }
      if (_statusEl) _statusEl.textContent = "Trocando câmera...";
      await _startWithPreferredCamera();
      await refreshCameras();
      if (_statusEl) _statusEl.textContent = "Procurando código...";
      _timer = setInterval(_capture, CAPTURE_INTERVAL_MS);
    } catch (error) {
      Utils.toast("Não foi possível trocar a câmera: " + error.message, "error");
    } finally {
      _switching = false;
    }
  }

  async function _capture() {
    const now = Date.now();
    if (_decoding || now < _retryAt || now - _lastReadAt < READ_COOLDOWN_MS) return;
    if (!_videoEl || !_canvasEl || _videoEl.readyState < 2) return;

    const maxEdge = 640;
    const scale = Math.min(1, maxEdge / Math.max(_videoEl.videoWidth, _videoEl.videoHeight));
    const width = Math.max(1, Math.round(_videoEl.videoWidth * scale));
    const height = Math.max(1, Math.round(_videoEl.videoHeight * scale));
    const ctx = _canvasEl.getContext("2d", { willReadFrequently: true });
    if (!ctx) return;

    _canvasEl.width = width;
    _canvasEl.height = height;
    ctx.drawImage(_videoEl, 0, 0, width, height);
    const imageData = ctx.getImageData(0, 0, width, height);

    const jsQr = typeof window.jsQR === "function" ? window.jsQR : null;
    if (jsQr) {
      _decoding = true;
      try {
        const result = jsQr(imageData.data, imageData.width, imageData.height, {
          inversionAttempts: "attemptBoth",
        });
        if (result?.data) {
          const candidate = String(result.data).trim();
          if (candidate && candidate !== _lastDecodedValue) {
            _lastDecodedValue = candidate;
            _lastReadAt = Date.now();
            _onFound({ primary: candidate, type: "unknown", data: null, codes: [candidate], source: "client" });
            return;
          }
        }
      } finally {
        _decoding = false;
      }
    }

    const detector = _getBarcodeDetector();
    if (detector && typeof detector.detect === "function") {
      _decoding = true;
      try {
        const detected = await detector.detect(_canvasEl);
        if (detected?.length) {
          const primary = String(detected[0].rawValue || detected[0].displayValue || "").trim();
          if (primary && primary !== _lastDecodedValue) {
            _lastDecodedValue = primary;
            _lastReadAt = Date.now();
            _onFound({ primary, type: "unknown", data: null, codes: [primary], source: "client" });
            return;
          }
        }
      } catch {
        _retryAt = Date.now() + 2500;
        if (_statusEl) _statusEl.textContent = "Não consegui ler ainda. Aponte melhor o QR ou troque a câmera.";
      } finally {
        _decoding = false;
      }
    }
  }

  function _onFound(result) {
    const callback = _callback;
    const inputId = _inputId;
    stop();
    if (inputId) {
      const el = document.getElementById(inputId);
      if (el) {
        el.value = result.primary;
        el.dispatchEvent(new Event("input"));
      }
    }
    if (typeof callback === "function") callback(result);
    Utils.toast(`✅ Código lido — tipo: ${result.type || "desconhecido"}`, "success");
  }

  function stop() {
    clearInterval(_timer);
    _timer = null;

    if (_escHandler) document.removeEventListener("keydown", _escHandler);
    _escHandler = null;

    if (_stream) {
      _stream.getTracks().forEach((track) => track.stop());
      _stream = null;
    }

    _container?.remove();
    _container = null;
    _callback = null;
    _inputId = null;
    _preferredCameraId = null;
    _availableCameras = [];
    _switching = false;
    _decoding = false;
    _retryAt = 0;
    _lastDecodedValue = "";
    _lastReadAt = 0;
    _barcodeDetector = null;
    _videoEl = null;
    _canvasEl = null;
    _statusEl = null;
    _selectEl = null;
    _cancelBtnEl = null;
    _refreshBtnEl = null;
  }

  return {
    async start(inputId, cb) {
      if (_stream || _container) stop();
      _inputId = inputId;
      _callback = cb;
      _buildUI();

      _escHandler = (event) => {
        if (event.key === "Escape") stop();
      };
      document.addEventListener("keydown", _escHandler);

      try {
        if (_statusEl) _statusEl.textContent = "Solicitando permissão da câmera...";
        await _startWithPreferredCamera();
        await refreshCameras();
        if (_statusEl) _statusEl.textContent = "Procurando código...";
        clearInterval(_timer);
        _timer = setInterval(_capture, CAPTURE_INTERVAL_MS);
      } catch (error) {
        if (_statusEl) _statusEl.textContent = "Câmera indisponível.";
        Utils.toast("Câmera indisponível: " + error.message, "error");
        stop();
      }
    },
    stop,
    destroy() { stop(); },
    refreshCameras,
    switchCamera,
  };
})();

window.QRScanner = QRScanner;