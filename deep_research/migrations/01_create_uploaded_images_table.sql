-- Migration: Create uploaded_images table (simplified schema)
-- This is the current simplified schema without foreign key dependencies
-- Run this in Supabase SQL Editor for fresh installations

-- Create the uploaded_images table
CREATE TABLE IF NOT EXISTS uploaded_images (
  doc_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  storage_path TEXT NOT NULL UNIQUE,
  storage_url TEXT NOT NULL,
  file_name TEXT NOT NULL,
  file_size BIGINT NOT NULL,
  mime_type TEXT NOT NULL,
  uploaded_at TIMESTAMPTZ DEFAULT NOW(),
  is_active BOOLEAN DEFAULT true,
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_uploaded_images_uploaded_at ON uploaded_images(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_uploaded_images_is_active ON uploaded_images(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_uploaded_images_metadata ON uploaded_images USING GIN (metadata);

-- Disable RLS (access control is handled via application-level authentication)
ALTER TABLE uploaded_images DISABLE ROW LEVEL SECURITY;

-- Add comments
COMMENT ON TABLE uploaded_images IS 'Tracks metadata for images uploaded by users for agent analysis';
COMMENT ON COLUMN uploaded_images.doc_id IS 'Unique document identifier for the uploaded image';
COMMENT ON COLUMN uploaded_images.storage_path IS 'Path in Supabase Storage bucket';
COMMENT ON COLUMN uploaded_images.storage_url IS 'Full URL to access the image (signed URL for private buckets)';
COMMENT ON COLUMN uploaded_images.metadata IS 'JSON metadata for the image, can include user_id and other custom fields';

