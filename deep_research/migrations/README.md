# Image Upload Feature - Setup Instructions

This directory contains database migrations and setup for the image upload feature that allows users to upload photos for agent analysis.

## Setup Steps

### 1. Create Database Table

Run the table creation script in Supabase SQL Editor:

```sql
-- Run: migrations/01_create_uploaded_images_table.sql
```

This creates:
- `uploaded_images` table with simplified schema (no foreign key dependencies)
- Indexes for efficient queries
- Metadata JSONB field for storing user_id and other custom fields
- RLS disabled (access control handled via application-level authentication)

### 2. Create Storage Bucket

Run the storage bucket creation script in Supabase SQL Editor:

```sql
-- Run: migrations/02_create_storage_bucket.sql
```

This creates:
- A private storage bucket named `user-uploads`
- File size limit: 10MB
- Allowed types: JPEG, PNG, GIF, WebP

### 3. Environment Variables

Ensure these are set in your `.env` file:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
POSTGRES_URI=postgresql://postgres:password@host:5432/postgres
```

### 4. API Endpoints

The image upload endpoints are available at:

- **Create**: `POST /api/v1/upload-image`
- **Read**: `GET /api/v1/upload-image/{doc_id}`
- **Delete**: `DELETE /api/v1/upload-image/{doc_id}`

**Create Request:**
- Content-Type: `multipart/form-data`
- Headers: `Authorization: Bearer <jwt_token>`
- Form fields:
  - `file`: The image file (required)

**Create Response:**
```json
{
  "doc_id": "uuid",
  "storage_url": "https://...",
  "storage_path": "timestamp-filename.jpg",
  "file_name": "original-filename.jpg",
  "file_size": 12345,
  "mime_type": "image/jpeg",
  "uploaded_at": "2024-01-01T12:00:00Z",
  "metadata": {
    "user_id": "user-uuid"
  }
}
```

## Usage in Frontend

After uploading, use the `storage_url` in your message content:

```typescript
const message = {
  type: "human",
  content: [
    { type: "text", text: "Analyze this image" },
    { 
      type: "image_url", 
      image_url: { url: response.storage_url } 
    }
  ]
};
```

## Database Schema

### `uploaded_images` Table

```sql
CREATE TABLE uploaded_images (
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
```

**Key Features:**
- Simplified schema without foreign key dependencies
- `user_id` stored in `metadata` JSONB field
- No `thread_id`, `message_id`, `run_id`, or `checkpoint_id` columns
- RLS disabled (access control via application-level authentication)

## Security

- ✅ Authentication required (Bearer token)
- ✅ File type validation (images only)
- ✅ File size limits (10MB)
- ✅ Application-level access control (user_id in metadata)
- ✅ Signed URLs for private bucket access

## Troubleshooting

### "Storage upload failed"
- Check that `SUPABASE_SERVICE_KEY` is set correctly
- Verify the storage bucket exists
- Ensure both `Authorization` and `apikey` headers are included

### "Database insert failed"
- Verify `POSTGRES_URI` is correct
- Check that `uploaded_images` table exists
- Verify the table schema matches the migration

### "Invalid file type"
- Only image files are allowed (JPEG, PNG, GIF, WebP)
- Check the file's MIME type

### "File too large"
- Maximum file size is 10MB
- Compress images before uploading if needed

### "Invalid image URL" error from AI
- Ensure signed URLs include `/storage/v1` prefix
- Check that the signed URL format is correct
