/**
 * assets/js/lib/supabase-config.js
 * Configuração do Supabase para uso direto no frontend.
 * Usado para autenticação de usuários e fallback offline.
 */

// Define as variáveis globais de forma segura, evitando erro se o arquivo for carregado
// mais de uma vez no navegador.
window.SUPABASE_URL = window.SUPABASE_URL || "https://jwncagbmqipbzoeldlet.supabase.co";
window.SUPABASE_KEY = window.SUPABASE_KEY || "sb_publishable_erfwnkHOevFoIX1pHN-9-g_i8xcqPkX";

window._sbFrontend = window._sbFrontend || null;

function getSupabaseFrontend() {
  if (!window._sbFrontend && window.supabase) {
    window._sbFrontend = window.supabase.createClient(window.SUPABASE_URL, window.SUPABASE_KEY);
  }
  return window._sbFrontend;
}