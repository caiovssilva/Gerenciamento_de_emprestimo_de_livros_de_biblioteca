/**
 * assets/js/lib/supabase-config.js
 * Configuração do Supabase para uso direto no frontend.
 * IMPORTANTE: As credenciais são carregadas dinamicamente do backend por segurança.
 * Nunca hardcode credenciais Supabase no frontend.
 */

// Placeholder - serão preenchidas dinamicamente via API.loadSupabaseConfig()
window.SUPABASE_URL = null;
window.SUPABASE_KEY = null;

// Função para carregar credenciais de forma segura (CSRF protegida)
async function loadSupabaseConfig() {
  const endpoints = [
    "/api/auth/config/supabase",
    "/api/config/supabase",
    "/api/auth/supabase-config",
    "/api/supabase-config",
  ];
  let lastError = null;

  for (const endpoint of endpoints) {
    try {
      const res = await fetch(endpoint);
      if (!res.ok) {
        lastError = new Error(`HTTP ${res.status}`);
        continue;
      }

      const data = await res.json();
      if (!data?.url || !data?.key) {
        lastError = new Error("Configuração Supabase ausente");
        continue;
      }

      window.SUPABASE_URL = data.url;
      window.SUPABASE_KEY = data.key;
      return data;
    } catch (error) {
      lastError = error;
    }
  }

  console.debug("Supabase ausente — usando fallback local.", lastError?.message || "sem detalhes");
  window.SUPABASE_URL = "";
  window.SUPABASE_KEY = "";
  return null;
}

window._sbFrontend = window._sbFrontend || null;

function getSupabaseFrontend() {
  if (!window._sbFrontend && window.supabase && window.SUPABASE_URL && window.SUPABASE_KEY) {
    window._sbFrontend = window.supabase.createClient(window.SUPABASE_URL, window.SUPABASE_KEY);
  }
  return window._sbFrontend;
}