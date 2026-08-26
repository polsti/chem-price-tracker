import { createClient } from "@supabase/supabase-js";

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY
);

// Drop-in replacement for fetch() that automatically attaches the
// logged-in user's token as an Authorization header — this is what
// api.py's require_login() checks for on every protected route.
export async function authFetch(url, options = {}) {
  const { data: { session } } = await supabase.auth.getSession();

  const headers = {
    ...options.headers,
    ...(session ? { Authorization: `Bearer ${session.access_token}` } : {}),
  };

  return fetch(url, { ...options, headers });
}
