# Music Library

Complete guide to the Music Library feature, including library browsing, playlist management, CSV import, and Spotify integration.

## Overview

The Music Library is a personal music management system that allows you to:
- **Browse & Search**: Navigate your music collection with filters and sorting
- **Manage Playlists**: Create, organize, and sync playlists
- **Import Music**: Bulk import tracks via CSV export from Spotify
- **Spotify Sync**: Two-way synchronization with your Spotify account

---

## Features

### Music Library Browser

Access your entire music collection with powerful filtering:

| Feature | Description |
|---------|-------------|
| **Paginated View** | 20 songs per page with navigation |
| **Search** | Search by track name, artist, or album |
| **Explicit Filter** | Filter explicit/clean content |
| **Popularity Filter** | Filter by minimum popularity score |
| **Sorting** | Sort by track, artist, album, release date, popularity, or tempo |
| **Song Details** | Modal view with full metadata and audio features |

**Access**: Navigate to `/music/library`

### Playlist Management

Create and manage personal playlists:

- **Create Playlists**: Name and optional description
- **Add/Remove Songs**: Build playlists from your library
- **Reorder Songs**: Drag-and-drop song ordering
- **Bulk Add**: Add multiple songs at once
- **Total Duration**: Auto-calculated playlist length

**Access**: Navigate to `/music/playlists`

### CSV Import

Import your Spotify library via CSV export:

1. Export your Spotify library using [Exportify](https://exportify.net/) or similar tools
2. Upload the CSV file to the import dialog
3. Monitor real-time import progress
4. Review import summary (inserted, duplicates, errors)

**Supported CSV Columns**:

| Column | Required | Description |
|--------|----------|-------------|
| `Track URI` | ✅ Yes | Spotify track URI (e.g., `spotify:track:...`) |
| `Track Name` | No | Song title |
| `Album Name` | No | Album title |
| `Artist Name(s)` | No | Artist(s) |
| `Release Date` | No | Release date |
| `Duration (ms)` | No | Track duration in milliseconds |
| `Popularity` | No | Spotify popularity score (0-100) |
| `Explicit` | No | True/False |
| `Added By` | No | Who added the track |
| `Added At` | No | When it was added |
| `Genres` | No | Comma-separated genres |
| `Record Label` | No | Record label |

**Audio Features** (optional):
- Danceability, Energy, Key, Loudness, Mode
- Speechiness, Acousticness, Instrumentalness
- Liveness, Valence, Tempo, Time Signature

### Spotify Integration

Connect your Spotify account for two-way sync:

| Feature | Description | Access |
|---------|-------------|--------|
| **Connect** | OAuth login to Spotify | Admin only |
| **Disconnect** | Remove Spotify connection | Admin only |
| **Export Playlist** | Push local playlist to Spotify | All users |
| **Import Playlist** | Pull Spotify playlist to local | All users |
| **View Playlists** | Browse Spotify playlists | All users |

---

## Getting Started

### Prerequisites

1. **User Account**: Log in to access the music features
2. **Spotify Credentials** (for sync): Admin must configure OAuth
   ```bash
   # In your .env file
   SPOTIPY_CLIENT_ID=your_client_id
   SPOTIPY_CLIENT_SECRET=your_client_secret
   SPOTIPY_REDIRECT_URI=http://localhost:5000/music/spotify/callback
   ```

### Importing Your Music

1. **Export from Spotify**: Use [Exportify](https://exportify.net/) to download your library as CSV
2. **Upload CSV**: Go to Music Library → Click "Import" → Select CSV file
3. **Monitor Progress**: Watch the import status (queued → running → completed)
4. **Review Results**: Check inserted, duplicate, and error counts

### Creating Your First Playlist

1. Navigate to `/music/playlists`
2. Click "Create Playlist"
3. Enter a name and optional description
4. Go to the library (`/music/library`)
5. Click on songs to view details → "Add to Playlist"

### Connecting Spotify (Admin)

1. Navigate to Music Playlists page
2. Click "Connect Spotify" (admin only)
3. Authorize the application in Spotify
4. After redirect, connection is complete

---

## Usage Guide

### Browsing the Library

1. Navigate to `/music/library`
2. Use the search box for text search
3. Apply filters:
   - **Explicit**: Show only explicit or clean tracks
   - **Min Popularity**: Filter by Spotify popularity
4. Click column headers to sort
5. Click any song to view full details in a modal

### Managing Playlists

**Create a Playlist**:
1. Go to `/music/playlists`
2. Click "Create Playlist"
3. Enter name and description
4. Click "Create"

**Add Songs**:
1. From the library, click a song
2. In the modal, select "Add to Playlist"
3. Choose the target playlist

**Remove Songs**:
1. Open the playlist
2. Click the remove icon next to any song

**Reorder Songs**:
1. Open the playlist
2. Drag songs to reorder
3. Order is saved automatically

### Exporting to Spotify

1. Open the playlist you want to export
2. Click "Export to Spotify"
3. Choose public or private visibility
4. Wait for sync to complete
5. Find the playlist in your Spotify account

### Importing from Spotify

1. Ensure Spotify is connected
2. Go to "Spotify Playlists" section
3. Click "Import" next to any playlist
4. Choose a name (or use original)
5. Note: Only songs already in your local library will be added

---

## Technical Details

### Database Models

**Song** (`songs` table):
- Primary key: `track_uri` (Spotify URI)
- Indexed fields: `track_name`, `artist_names`, `popularity`, `explicit`
- 20+ fields including audio features

**Playlist** (`playlists` table):
- User-owned with `user_id` foreign key
- Optional Spotify sync fields (`spotify_playlist_id`, `spotify_synced_at`)

**playlist_songs** (association table):
- Many-to-many relationship
- Includes `position` for song ordering

**MusicImportJob** (`music_import_jobs` table):
- UUID primary key
- Progress tracking: `total_rows`, `processed_rows`, `inserted_count`, `duplicate_count`, `error_count`
- Status: `queued` → `running` → `completed` or `failed`

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/music/library` | GET | Library page with filters |
| `/music/library/song` | GET | Song details (JSON) |
| `/music/library/import` | POST | Start CSV import |
| `/music/library/import-status` | GET | Import job status |
| `/music/playlists` | GET | List user playlists |
| `/music/playlists/<id>` | GET | View playlist |
| `/music/playlists/create` | POST | Create playlist |
| `/music/playlists/<id>/update` | POST | Update playlist |
| `/music/playlists/<id>` | DELETE | Delete playlist |
| `/music/playlists/<id>/add-songs` | POST | Add songs (bulk) |
| `/music/playlists/<id>/remove-song` | DELETE | Remove song |
| `/music/playlists/<id>/reorder` | POST | Reorder songs |
| `/music/spotify/authorize` | GET | Start OAuth (admin) |
| `/music/spotify/callback` | GET | OAuth callback |
| `/music/spotify/status` | GET | Check auth status |
| `/music/spotify/disconnect` | POST | Remove auth (admin) |
| `/music/playlists/<id>/export-to-spotify` | POST | Export to Spotify |
| `/music/spotify/playlists` | GET | List Spotify playlists |
| `/music/spotify/playlists/<id>/import` | POST | Import from Spotify |

### Background Processing

CSV imports run in background threads:
1. User uploads CSV → Job created with `queued` status
2. Background thread starts → Status: `running`
3. Rows processed in batches of 50
4. Progress updates every 25 rows
5. Completion → Status: `completed` or `failed`
6. Uploaded file is automatically cleaned up

---

## Troubleshooting

### Import Issues

**"Missing Track URI"**
- The CSV must have a `Track URI` column
- Ensure you're using the Spotify export format

**Many Duplicates**
- Songs with the same Track URI are skipped
- This is expected if re-importing the same library

**Import Stuck**
- Check application logs for errors
- Restart the application if needed

### Spotify Connection Issues

**"Spotify OAuth configuration missing"**
- Ensure `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, and `SPOTIPY_REDIRECT_URI` are set in `.env`

**"No valid Spotify authentication found"**
- Admin needs to connect to Spotify first
- Go to playlists page and click "Connect Spotify"

**"Token expired and refresh failed"**
- Disconnect and reconnect to Spotify
- This refreshes all tokens

### Playlist Export Issues

**"Playlist is empty"**
- Add songs to the playlist before exporting

**Songs not found on Spotify during import**
- Only tracks that exist in your local library can be added
- Import your library first, then import playlists

---

## Best Practices

1. **Import Library First**: Import your full Spotify library before importing playlists
2. **Use Exportify**: Best tool for exporting Spotify data with all metadata
3. **Regular Exports**: Re-export periodically to get new songs
4. **Playlist Organization**: Create playlists locally, then sync to Spotify
5. **Check Import Status**: Monitor long imports via the status endpoint

---

## Related Documentation

- [Architecture Overview](ARCHITECTURE.md) - System architecture
- [Features Overview](FEATURES.md) - All features
- [Main README](../README.md) - Setup and installation
