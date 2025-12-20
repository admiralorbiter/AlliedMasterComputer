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

    // Song row click handler - show details modal
    document.querySelectorAll('.song-row').forEach(function(row) {
        row.addEventListener('click', function(e) {
            // Don't trigger if clicking on a link or button
            if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON') {
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

