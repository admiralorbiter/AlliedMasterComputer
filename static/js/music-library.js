// Music Library JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token helper
    function getCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        return null;
    }

    // Table header sorting
    document.querySelectorAll('.table thead th.sortable').forEach(function(header) {
        header.addEventListener('click', function(e) {
            const sortField = this.dataset.sort;
            if (!sortField) return;
            
            // Get current sort parameters from URL
            const urlParams = new URLSearchParams(window.location.search);
            const currentSort = urlParams.get('sort_by');
            const currentOrder = urlParams.get('sort_order') || 'asc';
            
            // Determine new sort order
            let newOrder = 'asc';
            if (currentSort === sortField && currentOrder === 'asc') {
                newOrder = 'desc';
            }
            
            // Update URL parameters
            urlParams.set('sort_by', sortField);
            urlParams.set('sort_order', newOrder);
            urlParams.set('page', '1'); // Reset to first page when sorting
            
            // Navigate to new URL
            window.location.href = window.location.pathname + '?' + urlParams.toString();
        });
    });

    // Song row click handler - show details modal
    document.querySelectorAll('.song-row').forEach(function(row) {
        row.addEventListener('click', function(e) {
            // Don't trigger if clicking on a link, button, or checkbox
            if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON' || 
                e.target.tagName === 'INPUT' || e.target.closest('input[type="checkbox"]')) {
                return;
            }
            
            const trackUri = this.dataset.trackUri;
            if (!trackUri) {
                return;
            }
            
            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('songDetailsModal'));
            const modalContent = document.getElementById('songDetailsContent');
            
            // Show loading state
            modalContent.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                </div>
            `;
            
            modal.show();
            
            // Fetch song details
            fetch(`/music/library/song?track_uri=${encodeURIComponent(trackUri)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        modalContent.innerHTML = `
                            <div class="alert alert-danger">
                                <i class="fas fa-exclamation-circle"></i> ${data.error}
                            </div>
                        `;
                        return;
                    }
                    
                    // Format song details
                    modalContent.innerHTML = formatSongDetails(data);
                })
                .catch(error => {
                    console.error('Error fetching song details:', error);
                    modalContent.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-circle"></i> Error loading song details. Please try again.
                        </div>
                    `;
                });
        });
    });
    
    // ========== PLAYLIST FUNCTIONALITY ==========
    
    // Load user playlists
    let userPlaylists = [];
    function loadUserPlaylists() {
        return fetch('/music/playlists/user-playlists')
            .then(response => response.json())
            .then(data => {
                if (Array.isArray(data)) {
                    userPlaylists = data;
                    return data;
                } else {
                    console.error('Invalid playlists data:', data);
                    return [];
                }
            })
            .catch(error => {
                console.error('Error loading playlists:', error);
                return [];
            });
    }
    
    // Add song to playlist
    function addSongToPlaylist(playlistId, trackUris) {
        fetch(`/music/playlists/${playlistId}/add-songs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ track_uris: trackUris })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error adding songs: ' + data.error);
                return;
            }
            
            const added = data.added_count || 0;
            const errors = data.error_count || 0;
            
            if (added > 0) {
                // Show success message
                const playlist = userPlaylists.find(p => p.id === parseInt(playlistId));
                const playlistName = playlist ? playlist.name : 'playlist';
                showNotification(`Added ${added} song(s) to ${playlistName}`, 'success');
            }
            
            if (errors > 0) {
                showNotification(`Some songs could not be added (${errors} error(s))`, 'warning');
            }
        })
        .catch(error => {
            console.error('Error adding songs to playlist:', error);
            alert('Error adding songs to playlist. Please try again.');
        });
    }
    
    // Bulk selection functionality
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const songCheckboxes = document.querySelectorAll('.song-checkbox');
    const bulkActions = document.getElementById('bulkActions');
    const selectedCount = document.getElementById('selectedCount');
    const bulkAddToPlaylistBtn = document.getElementById('bulkAddToPlaylistBtn');
    
    function updateBulkActions() {
        const checked = Array.from(songCheckboxes).filter(cb => cb.checked);
        const count = checked.length;
        
        if (count > 0) {
            bulkActions.style.display = 'flex';
            selectedCount.textContent = `${count} selected`;
        } else {
            bulkActions.style.display = 'none';
        }
    }
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            songCheckboxes.forEach(cb => {
                cb.checked = this.checked;
            });
            updateBulkActions();
        });
    }
    
    songCheckboxes.forEach(cb => {
        cb.addEventListener('change', function() {
            // Update select all checkbox
            if (selectAllCheckbox) {
                const allChecked = Array.from(songCheckboxes).every(c => c.checked);
                const someChecked = Array.from(songCheckboxes).some(c => c.checked);
                selectAllCheckbox.checked = allChecked;
                selectAllCheckbox.indeterminate = someChecked && !allChecked;
            }
            updateBulkActions();
        });
    });
    
    // Bulk add to playlist
    if (bulkAddToPlaylistBtn) {
        bulkAddToPlaylistBtn.addEventListener('click', function() {
            const checked = Array.from(songCheckboxes).filter(cb => cb.checked);
            if (checked.length === 0) {
                alert('Please select at least one song');
                return;
            }
            
            const trackUris = checked.map(cb => cb.value);
            const bulkModal = new bootstrap.Modal(document.getElementById('bulkAddToPlaylistModal'));
            const bulkCount = document.getElementById('bulkAddCount');
            const bulkOptions = document.getElementById('bulkPlaylistOptions');
            
            bulkCount.textContent = trackUris.length;
            
            // Load playlists into modal
            bulkOptions.innerHTML = '<div class="text-center p-3"><div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">Loading...</span></div></div>';
            bulkModal.show();
            
            loadUserPlaylists().then(() => {
                if (userPlaylists.length === 0) {
                    bulkOptions.innerHTML = '<div class="text-muted p-3">No playlists yet. Create one below.</div>';
                } else {
                    let html = '<div class="list-group">';
                    userPlaylists.forEach(playlist => {
                        html += `
                            <a href="#" class="list-group-item list-group-item-action bulk-playlist-item" data-playlist-id="${playlist.id}">
                                <i class="fas fa-list"></i> ${playlist.name}
                                <small class="text-muted">(${playlist.song_count} songs)</small>
                            </a>
                        `;
                    });
                    html += '</div>';
                    bulkOptions.innerHTML = html;
                    
                    // Add click handlers
                    bulkOptions.querySelectorAll('.bulk-playlist-item').forEach(item => {
                        item.addEventListener('click', function(e) {
                            e.preventDefault();
                            const playlistId = this.dataset.playlistId;
                            bulkModal.hide();
                            addSongToPlaylist(playlistId, trackUris);
                            // Uncheck all
                            songCheckboxes.forEach(cb => cb.checked = false);
                            if (selectAllCheckbox) selectAllCheckbox.checked = false;
                            updateBulkActions();
                        });
                    });
                }
            });
        });
    }
    
    // Create playlist from bulk
    const createPlaylistFromBulkModal = document.getElementById('createPlaylistFromBulkModal');
    if (createPlaylistFromBulkModal) {
        document.getElementById('createPlaylistFromBulkSubmit')?.addEventListener('click', function() {
            const form = document.getElementById('createPlaylistFromBulkForm');
            const name = document.getElementById('createPlaylistFromBulkName').value.trim();
            const description = document.getElementById('createPlaylistFromBulkDescription').value.trim();
            
            if (!name) {
                alert('Playlist name is required');
                return;
            }
            
            const checked = Array.from(songCheckboxes).filter(cb => cb.checked);
            const trackUris = checked.map(cb => cb.value);
            
            if (trackUris.length === 0) {
                alert('Please select at least one song');
                return;
            }
            
            fetch('/music/playlists/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, description: description || null })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error creating playlist: ' + data.error);
                    return;
                }
                
                // Add songs to new playlist
                addSongToPlaylist(data.id, trackUris);
                
                // Reload playlists
                loadUserPlaylists().then(() => {
                    bootstrap.Modal.getInstance(createPlaylistFromBulkModal).hide();
                    form.reset();
                    // Uncheck all
                    songCheckboxes.forEach(cb => cb.checked = false);
                    if (selectAllCheckbox) selectAllCheckbox.checked = false;
                    updateBulkActions();
                    showNotification(`Playlist "${data.name}" created with ${trackUris.length} song(s)!`, 'success');
                });
            })
            .catch(error => {
                console.error('Error creating playlist:', error);
                alert('Error creating playlist. Please try again.');
            });
        });
    }
    
    // Notification helper
    function showNotification(message, type = 'info') {
        // Create a simple toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'info'} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
    
    // Load playlists on page load
    loadUserPlaylists();
    
    // Format song details for display
    function formatSongDetails(song) {
        const formatValue = (value) => {
            if (value === null || value === undefined || value === '') {
                return '<span class="empty">—</span>';
            }
            return String(value);
        };
        
        const formatFloat = (value, decimals = 2) => {
            if (value === null || value === undefined) {
                return '<span class="empty">—</span>';
            }
            const num = Number(value).toFixed(decimals);
            return `<span style="font-weight: 600; color: #6c5ce7;">${num}</span>`;
        };
        
        const formatBool = (value) => {
            if (value === null || value === undefined) {
                return '<span class="empty">—</span>';
            }
            return value ? '<span class="badge bg-danger">Yes</span>' : '<span class="badge bg-success">No</span>';
        };
        
        const formatDuration = (ms) => {
            if (!ms) return '<span class="empty">—</span>';
            const seconds = Math.floor(ms / 1000);
            const minutes = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `<span style="font-weight: 600; color: #2c3e50;">${minutes}:${secs.toString().padStart(2, '0')}</span>`;
        };
        
        const formatPopularity = (value) => {
            if (value === null || value === undefined) {
                return '<span class="empty">—</span>';
            }
            return `<span class="badge bg-info">${value}</span>`;
        };
        
        // Format Key value - show pitch class notation
        const formatKey = (value) => {
            if (value === null || value === undefined) {
                return '<span class="empty">—</span>';
            }
            const pitchClasses = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
            return pitchClasses[value] || String(value);
        };
        
        // Extract track ID from Spotify URI
        const extractTrackId = (trackUri) => {
            if (!trackUri) return null;
            // Format: spotify:track:1CPZ5BxNNd0n0nF40rb9JS
            const match = trackUri.match(/spotify:track:([a-zA-Z0-9]+)/);
            return match ? match[1] : null;
        };
        
        // Generate Spotify player HTML
        const getSpotifyPlayer = (trackUri) => {
            const trackId = extractTrackId(trackUri);
            if (!trackId) {
                return '<div class="spotify-player-container" style="padding: 1rem; background: #f8f9fa; border-radius: 8px; text-align: center; color: #6c757d;"><i class="fas fa-exclamation-circle"></i> Invalid track URI - cannot load player</div>';
            }
            const embedUrl = `https://open.spotify.com/embed/track/${trackId}`;
            return `
                <div class="spotify-player-container">
                    <iframe 
                        src="${embedUrl}" 
                        width="100%" 
                        height="152" 
                        frameborder="0" 
                        allowtransparency="true" 
                        allow="encrypted-media"
                        loading="lazy">
                    </iframe>
                </div>
            `;
        };
        
        // Use a more compact grid layout
        return `
            ${getSpotifyPlayer(song.track_uri)}
            <div class="song-details-grid">
            <div class="song-detail-item" style="grid-column: 1 / -1;">
                <div class="song-detail-label">Track URI</div>
                <div class="song-detail-value"><code>${formatValue(song.track_uri)}</code></div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Track Name</div>
                <div class="song-detail-value">${formatValue(song.track_name)}</div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Album Name</div>
                <div class="song-detail-value">${formatValue(song.album_name)}</div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Artist Name(s)</div>
                <div class="song-detail-value">${formatValue(song.artist_names)}</div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Release Date</div>
                <div class="song-detail-value">${formatValue(song.release_date)}</div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Duration (ms)</div>
                <div class="song-detail-value">${formatDuration(song.duration_ms)} <span style="color: #6c757d; font-weight: normal; font-size: 0.85em;">(${song.duration_ms ? song.duration_ms.toLocaleString() : '—'} ms)</span></div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Popularity</div>
                <div class="song-detail-value">${formatPopularity(song.popularity)}</div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Explicit</div>
                <div class="song-detail-value">${formatBool(song.explicit)}</div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Added By</div>
                <div class="song-detail-value">${formatValue(song.added_by)}</div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Added At</div>
                <div class="song-detail-value">${formatValue(song.added_at)}</div>
            </div>
            <div class="song-detail-item" style="grid-column: 1 / -1;">
                <div class="song-detail-label">Genres</div>
                <div class="song-detail-value">${formatValue(song.genres)}</div>
            </div>
            <div class="song-detail-item" style="grid-column: 1 / -1;">
                <div class="song-detail-label">Record Label</div>
                <div class="song-detail-value">${formatValue(song.record_label)}</div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Danceability</div>
                <div class="song-detail-value">${formatFloat(song.danceability)}</div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Energy</div>
                <div class="song-detail-value">${formatFloat(song.energy)}</div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Key</div>
                <div class="song-detail-value">${formatKey(song.key)}</div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Loudness</div>
                <div class="song-detail-value">${formatFloat(song.loudness)} <span style="color: #6c757d; font-weight: normal;">dB</span></div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Mode</div>
                <div class="song-detail-value">${song.mode === 1 ? 'Major' : song.mode === 0 ? 'Minor' : formatValue(song.mode)}</div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Speechiness</div>
                <div class="song-detail-value">${formatFloat(song.speechiness)}</div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Acousticness</div>
                <div class="song-detail-value">${formatFloat(song.acousticness)}</div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Instrumentalness</div>
                <div class="song-detail-value">${formatFloat(song.instrumentalness)}</div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Liveness</div>
                <div class="song-detail-value">${formatFloat(song.liveness)}</div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Valence</div>
                <div class="song-detail-value">${formatFloat(song.valence)}</div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Tempo</div>
                <div class="song-detail-value">${formatFloat(song.tempo, 1)} <span style="color: #6c757d; font-weight: normal;">BPM</span></div>
            </div>
            <div class="song-detail-item">
                <div class="song-detail-label">Time Signature</div>
                <div class="song-detail-value">${formatValue(song.time_signature)}</div>
            </div>
            </div>
        `;
    }
    
    // Import form handler
    const importForm = document.getElementById('importForm');
    const importSubmitBtn = document.getElementById('importSubmitBtn');
    const importCloseBtn = document.getElementById('importCloseBtn');
    const importProgress = document.getElementById('importProgress');
    const importProgressBar = document.getElementById('importProgressBar');
    const importStatusText = document.getElementById('importStatusText');
    const importStats = document.getElementById('importStats');
    
    if (importForm && importSubmitBtn) {
        importSubmitBtn.addEventListener('click', function() {
            const fileInput = document.getElementById('csvFile');
            if (!fileInput.files || fileInput.files.length === 0) {
                alert('Please select a CSV file');
                return;
            }
            
            // Disable submit button
            importSubmitBtn.disabled = true;
            importCloseBtn.disabled = true;
            
            // Show progress
            importProgress.style.display = 'block';
            importProgressBar.style.width = '0%';
            importProgressBar.textContent = '0%';
            importStatusText.textContent = 'Starting import...';
            importStats.textContent = '';
            
            // Create form data
            const formData = new FormData();
            formData.append('csv_file', fileInput.files[0]);
            
            // Submit import request
            fetch('/music/library/import', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error starting import: ' + data.error);
                    importSubmitBtn.disabled = false;
                    importCloseBtn.disabled = false;
                    importProgress.style.display = 'none';
                    return;
                }
                
                // Start polling for status
                const jobId = data.job_id;
                pollImportStatus(jobId);
            })
            .catch(error => {
                console.error('Error starting import:', error);
                alert('Error starting import. Please try again.');
                importSubmitBtn.disabled = false;
                importCloseBtn.disabled = false;
                importProgress.style.display = 'none';
            });
        });
    }
    
    // Poll import status
    function pollImportStatus(jobId) {
        const pollInterval = setInterval(function() {
            fetch(`/music/library/import-status?job_id=${jobId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        clearInterval(pollInterval);
                        importStatusText.textContent = 'Error: ' + data.error;
                        importSubmitBtn.disabled = false;
                        importCloseBtn.disabled = false;
                        return;
                    }
                    
                    // Update progress
                    const progress = data.progress_percent || 0;
                    importProgressBar.style.width = progress + '%';
                    importProgressBar.setAttribute('aria-valuenow', progress);
                    importProgressBar.textContent = progress + '%';
                    
                    // Update status text
                    if (data.status === 'queued') {
                        importStatusText.textContent = 'Queued...';
                    } else if (data.status === 'running') {
                        importStatusText.textContent = `Processing ${data.processed_rows} of ${data.total_rows} rows...`;
                    } else if (data.status === 'completed') {
                        clearInterval(pollInterval);
                        importStatusText.textContent = 'Import completed!';
                        importProgressBar.classList.remove('progress-bar-animated');
                        importSubmitBtn.disabled = false;
                        importCloseBtn.disabled = false;
                        
                        // Reload page after a short delay
                        setTimeout(function() {
                            window.location.reload();
                        }, 2000);
                    } else if (data.status === 'failed') {
                        clearInterval(pollInterval);
                        importStatusText.textContent = 'Import failed: ' + (data.error_message || 'Unknown error');
                        importSubmitBtn.disabled = false;
                        importCloseBtn.disabled = false;
                    }
                    
                    // Update stats
                    if (data.status === 'running' || data.status === 'completed') {
                        importStats.textContent = `
                            Inserted: ${data.inserted_count} | 
                            Duplicates: ${data.duplicate_count} | 
                            Errors: ${data.error_count}
                        `;
                    }
                })
                .catch(error => {
                    console.error('Error polling import status:', error);
                    clearInterval(pollInterval);
                    importStatusText.textContent = 'Error checking status';
                    importSubmitBtn.disabled = false;
                    importCloseBtn.disabled = false;
                });
        }, 1000); // Poll every second
    }
    
    // Reset import modal when closed
    const importModal = document.getElementById('importModal');
    if (importModal) {
        importModal.addEventListener('hidden.bs.modal', function() {
            importForm.reset();
            importProgress.style.display = 'none';
            importProgressBar.style.width = '0%';
            importProgressBar.textContent = '0%';
            importProgressBar.classList.add('progress-bar-animated');
            importStatusText.textContent = '';
            importStats.textContent = '';
            importSubmitBtn.disabled = false;
            importCloseBtn.disabled = false;
        });
    }
});

