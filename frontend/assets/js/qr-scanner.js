/**
 * assets/js/qr-scanner.js  —  v3
 * Câmera do browser → base64 → /api/qr/decode (resolve tipo automaticamente).
 */
const QRScanner = (() => {
  let _stream=null, _timer=null, _container=null, _callback=null, _inputId=null;

  function _buildUI() {
    const div=document.createElement("div");
    div.id="cam-container";
    div.innerHTML=`
      <h3><i class="ti ti-scan"></i> Aponte para o código</h3>
      <div class="cam-viewport">
        <video id="cam-video" autoplay playsinline muted></video>
        <canvas id="cam-canvas" style="display:none;"></canvas>
        <div class="cam-reticle"></div>
      </div>
      <p class="cam-status" id="cam-status">Inicializando câmera...</p>
      <button class="btn btn-danger" style="width:100%;margin-top:10px;" onclick="QRScanner.stop()">
        <i class="ti ti-x"></i> Cancelar
      </button>`;
    document.body.appendChild(div);
    return div;
  }

  async function _capture() {
    const video=document.getElementById("cam-video");
    const canvas=document.getElementById("cam-canvas");
    if (!video||!canvas||video.readyState<2) return;
    canvas.width=video.videoWidth; canvas.height=video.videoHeight;
    canvas.getContext("2d").drawImage(video,0,0);
    const b64=canvas.toDataURL("image/jpeg",0.8);
    try {
      const res=await API.qr.decode(b64);
      if (res.primary) _onFound(res);
    } catch { /* ignora frame */ }
  }

  function _onFound(result) {
    stop();
    // Preenche input se especificado, senão passa o resultado completo ao callback
    if (_inputId) {
      const el=document.getElementById(_inputId);
      if (el) { el.value=result.primary; el.dispatchEvent(new Event("input")); }
    }
    if (typeof _callback==="function") _callback(result);
    Utils.toast(`✅ Código lido — tipo: ${result.type||"desconhecido"}`,"success");
  }

  return {
    async start(inputId, cb) {
      if (_stream) return;
      _inputId=inputId; _callback=cb; _container=_buildUI();
      try {
        _stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:"environment"}});
        const v=document.getElementById("cam-video");
        v.srcObject=_stream; await v.play();
        const st=document.getElementById("cam-status");
        if (st) st.textContent="Procurando código...";
        _timer=setInterval(_capture,600);
      } catch(err) { Utils.toast("Câmera indisponível: "+err.message,"error"); stop(); }
    },
    stop() {
      clearInterval(_timer); _timer=null;
      if (_stream){_stream.getTracks().forEach(t=>t.stop());_stream=null;}
      _container?.remove(); _container=null; _callback=null; _inputId=null;
    },
  };
})();