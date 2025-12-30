# Supabase OAuth Implementation Guide

This document explains how to set up and use Supabase OAuth authentication with the Deep Agents application.

## Quick Start

### Step 1: Get Your Supabase Credentials

1. **Go to Supabase Dashboard**: [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. **Select your project** (or create a new one)
3. **Get Project URL**:
   - Go to **⚙️ Project Settings** → **API**
   - Copy the **Project URL** (e.g., `https://xxxxx.supabase.co`)
4. **Get Service Role Key** (for backend):
   - In the same **API** settings page
   - Find **Project API keys** section
   - Copy the **`service_role`** key (starts with `eyJ...`)
   - ⚠️ **SECRET** - Never expose in client code!
5. **Get Anon Public Key** (for frontend):
   - On the same page
   - Copy the **`anon`** `public` key
   - Safe for client-side use

### Step 2: Configure Backend

Add to your `.env` file in `deepagents-quickstarts/deep_research/`:

```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # service_role key
```

### Step 3: Configure Frontend

1. **Install dependencies**:
   ```bash
   cd deep-agents-ui
   yarn install
   ```

2. **Configure in UI**:
   - Open the app
   - Click **Settings**
   - Enter your **Supabase URL** and **Supabase Anon Key**
   - Save configuration

### Step 4: Test

1. **Start backend**:
   ```bash
   cd deepagents-quickstarts/deep_research
   langgraph dev --no-browser
   ```

2. **Start frontend**:
   ```bash
   cd deep-agents-ui
   yarn dev
   ```

3. **Test authentication**:
   - Open the app in browser
   - You should see a login dialog
   - Sign up with a new email/password
   - Check your email and confirm the account
   - Sign in with your credentials
   - You should now be able to access the agent

## How It Works

### Backend Authentication Flow

1. **User signs in** via Supabase (frontend)
2. **Supabase returns JWT token** to frontend
3. **Frontend sends token** in `Authorization: Bearer <token>` header
4. **Backend validates token** by calling Supabase API:
   ```python
   GET {SUPABASE_URL}/auth/v1/user
   Headers:
     Authorization: Bearer <token>
     apikey: <SUPABASE_SERVICE_KEY>
   ```
5. **Supabase validates token** and returns user info
6. **Backend extracts user identity** and allows request

### Frontend Authentication Flow

1. **User opens app** → Checks for saved auth token
2. **If no token** → Shows Supabase login dialog
3. **User signs up/signs in** → Supabase returns JWT token
4. **Token saved** to localStorage in config
5. **All API requests** include `Authorization: Bearer <token>` header
6. **Backend validates** token on each request

## Code Structure

### Backend Files

- **`security/auth.py`**: Validates Supabase JWT tokens
  - Uses `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` from environment
  - Calls Supabase API to validate tokens
  - Extracts user identity from validated token

### Frontend Files

- **`src/app/components/SupabaseLoginDialog.tsx`**: Login/signup UI
  - Uses `@supabase/supabase-js` client
  - Handles sign up and sign in
  - Returns JWT token to parent component

- **`src/lib/config.ts`**: Configuration storage
  - Stores `supabaseUrl` and `supabaseAnonKey`
  - Stores `authToken` (JWT from Supabase)

- **`src/providers/ClientProvider.tsx`**: API client setup
  - Adds `Authorization: Bearer <token>` to all requests

- **`src/app/page.tsx`**: Main page logic
  - Shows Supabase login if configured
  - Falls back to legacy token auth if not

## Environment Variables

### Backend (`.env` file)

```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...  # service_role key (SECRET)
```

### Frontend (Config Dialog or Environment)

- `supabaseUrl`: Your Supabase project URL
- `supabaseAnonKey`: Your Supabase anon/public key
- Stored in localStorage (not environment variables)

## Testing

### Manual Testing

1. **Test sign up**:
   - Open app
   - Click "Don't have an account? Sign up"
   - Enter email and password
   - Check email for confirmation link
   - Click confirmation link
   - Sign in

2. **Test sign in**:
   - Enter email and password
   - Should get access token
   - Should be able to create threads and chat

3. **Test token validation**:
   - Try accessing without token → Should fail
   - Try accessing with invalid token → Should fail
   - Try accessing with valid token → Should succeed

### Automated Testing

Run the test script:

```bash
cd deepagents-quickstarts/deep_research
export SUPABASE_URL=your-url
export SUPABASE_ANON_KEY=your-anon-key
python test_auth_supabase.py
```

## Troubleshooting

### "Invalid token" errors

- **Check backend environment**: Make sure `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are set
- **Verify service key**: Must be the `service_role` key, not the anon key
- **Check token format**: Should be a valid JWT token from Supabase

### "Email not confirmed" errors

- **Check email**: Supabase sends confirmation emails
- **Click confirmation link**: Required before first login
- **Check spam folder**: Confirmation emails might be filtered

### Frontend can't connect to Supabase

- **Check Supabase URL**: Must be correct project URL
- **Check anon key**: Must be the anon/public key (not service_role)
- **Check network**: Make sure you can reach Supabase API
- **Check CORS**: Supabase should allow requests from your domain

### "Authentication service unavailable" errors

- **Check backend logs**: See if Supabase API calls are failing
- **Check network**: Backend must be able to reach Supabase
- **Check credentials**: Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are correct

## Security Notes

1. **Service Role Key**: 
   - ⚠️ **NEVER** expose in client-side code
   - Only use in backend/server code
   - Has full access to your Supabase project

2. **Anon Key**:
   - Safe for client-side use
   - Limited permissions (defined by RLS policies)
   - Used for sign up/sign in

3. **JWT Tokens**:
   - Stored in localStorage (not encrypted)
   - Sent in HTTP headers (use HTTPS in production)
   - Validated on every request

4. **Email Confirmation**:
   - Supabase requires email confirmation by default
   - Can be disabled in Supabase dashboard (not recommended)

## Migration from Legacy Auth

If you were using the hardcoded token system:

1. **Add Supabase credentials** to config
2. **Users will see Supabase login** instead of token input
3. **Old tokens won't work** - users must sign up/sign in
4. **Legacy auth still works** if Supabase is not configured

## Next Steps

- [ ] Set up email templates in Supabase
- [ ] Configure password reset flow
- [ ] Add social OAuth providers (Google, GitHub, etc.)
- [ ] Implement session refresh
- [ ] Add user profile management
- [ ] Set up Row Level Security (RLS) policies in Supabase

