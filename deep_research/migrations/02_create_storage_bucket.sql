-- Migration: Create Supabase Storage bucket for user uploads
-- Run this in Supabase SQL Editor

-- Create the storage bucket (if it doesn't exist)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'user-uploads',
  'user-uploads',
  false,  -- Private bucket (users need auth to access)
  10485760,  -- 10MB file size limit (in bytes)
  ARRAY['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']  -- Only image types
)
ON CONFLICT (id) DO NOTHING;

-- Note: Storage RLS policies are not needed since we're using service role key
-- for uploads and signed URLs for access. If you need user-level access control,
-- you can add storage policies here.

-- Add comment
COMMENT ON BUCKET "user-uploads" IS 'Storage bucket for user-uploaded images that can be analyzed by the agent';

