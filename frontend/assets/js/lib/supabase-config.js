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
  const endpoints = ["/api/auth/config/supabase", "/api/config/supabase"];
  try {
    let lastError = null;
    for (const endpoint of endpoints) {
      try {
        const res = await fetch(endpoint);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!data?.url || !data?.key) throw new Error("Configuração Supabase ausente");
        window.SUPABASE_URL = data.url;
        window.SUPABASE_KEY = data.key;
        return data;
      } catch (error) {
        lastError = error;
      }
    }
    throw lastError || new Error("Configuração Supabase indisponível");
  } catch (error) {
    console.error("Erro ao carregar config Supabase:", error);
    return null;
  }
}

window._sbFrontend = window._sbFrontend || null;

function getSupabaseFrontend() {
  if (!window._sbFrontend && window.supabase) {
    window._sbFrontend = window.supabase.createClient(window.SUPABASE_URL, window.SUPABASE_KEY);
  }
  return window._sbFrontend;
}