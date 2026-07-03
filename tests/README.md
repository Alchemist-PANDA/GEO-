# Zero-cost auth for BrandSight GEO

Multi-user login (same access for everyone), built on Supabase Auth's
free tier. Nothing here costs money at any realistic scale for a
personal/small-team dashboard (free tier = 50,000 monthly active users).

## Why this is "unbroken" and not just "works for the demo"

The two most common ways a hand-rolled auth system breaks are:

1. **The UI check is the only check.** Someone hits your database's API
   directly (Supabase exposes a REST API automatically) and the data
   comes back with no login at all. `rls_policies.sql` fixes this by
   enforcing auth *inside Postgres itself* — the login screen becomes
   a convenience, not the security boundary.
2. **Homegrown password/session handling has a subtle bug** — a session
   that never expires, a password comparison that's not constant-time,
   a rate limit that's easy to bypass. This design puts zero password or
   session logic in your code. Supabase's Auth service (audited,
   widely-used, SOC2-compliant even on the free tier) owns all of that.

## Setup (15 minutes, $0)

1. Create a free project at supabase.com.
2. Run your existing `supabase_schema.sql`, then run `rls_policies.sql`
   from this folder (edit table names to match yours first).
3. In Supabase: Authentication -> Settings — decide if signup is open
   or invite-only (toggle "Allow new users to sign up").
4. Copy `secrets.toml.example` to `.streamlit/secrets.toml`, fill in
   your Project URL and **anon** key (Project Settings -> API).
   Add `.streamlit/secrets.toml` to `.gitignore` if it isn't already.
5. `pip install supabase extra-streamlit-components`
6. Wire `auth.py` into your app as shown in
   `example_dashboard_integration.py` — just those few lines at the
   top of `dashboard.py`.
7. Deploy (Streamlit Community Cloud is free). Paste the same secrets
   into the app's Secrets settings in the Community Cloud dashboard.

## Adding/removing users

Since everyone gets identical access, you don't manage roles — just
who has an account:
- **Invite-only:** turn off public signup (step 3), and create users
  yourself under Supabase -> Authentication -> Users -> "Add user".
- **Self-service:** leave signup open; the `sign_up` form in `auth.py`
  handles it, with email confirmation before first login.

To remove someone's access, delete their user in Supabase ->
Authentication -> Users. Their session is invalidated within one
refresh cycle.

## Files

- `auth.py` — the actual auth logic (import this into your app)
- `rls_policies.sql` — database-level enforcement (run once in Supabase)
- `secrets.toml.example` — template for your credentials
- `example_dashboard_integration.py` — copy-paste starting point
