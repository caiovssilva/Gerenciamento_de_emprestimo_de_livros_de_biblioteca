/**
 * assets/js/lib/supabase-config.js
 * Configuração do Supabase para uso direto no frontend.
 * Usado para autenticação de usuários e fallback offline.
 */

const SUPABASE_URL = "https://jwncagbmqipbzoeldlet.supabase.co";
const SUPABASE_KEY = "sb_publishable_erfwnkHOevFoIX1pHN-9-g_i8xcqPkX";

// Inicializa cliente Supabase (para auth / realtime direto no browser)
let _sbFrontend = null;

function getSupabaseFrontend() {
  if (!_sbFrontend && window.supabase) {
    _sbFrontend = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
  }
  return _sbFrontend;
}
