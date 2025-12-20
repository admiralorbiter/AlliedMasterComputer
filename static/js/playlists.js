// Playlists JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // ========== PLAYLIST LIST PAGE ==========
    
    // Create playlist
    const createPlaylistForm = document.getElementById('createPlaylistForm');
    const createPlaylistSubmit = document.getElementById('createPlaylistSubmit');
    
    if (createPlaylistSubmit) {
        createPlaylistSubmit.addEventListener('click', function() {
            const name = document.getElementById('playlistName').value.trim();
            const description = document.getElementById('playlistDescription').value.trim();
            
            if (!name) {
                alert('Playlist name is required');
                return;
            }
            
            createPlaylistSubmit.disabled = true;
            
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
                    createPlaylistSubmit.disabled = false;
                    return;
                }
                
                // Reload page
                window.location.reload();
            })
            .catch(error => {
                console.error('Error creating playlist:', error);
                alert('Error creating playlist. Please try again.');
                createPlaylistSubmit.disabled = false;
            });
        });
    }
    
    // Edit playlist
    const editPlaylistBtns = document.querySelectorAll('.playlist-edit-btn');
    const editPlaylistModal = document.getElementById('editPlaylistModal');
    
    editPlaylistBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const playlistId = this.dataset.playlistId;
            const playlistName = this.dataset.playlistName;
            const playlistDescription = this.dataset.playlistDescription || '';
            
            document.getElementById('editPlaylistId').value = playlistId;
            document.getElementById('editPlaylistName').value = playlistName;
            document.getElementById('editPlaylistDescription').value = playlistDescription;
            
            const modal = new bootstrap.Modal(editPlaylistModal);
            modal.show();
        });
    });
    
    const editPlaylistSubmit = document.getElementById('editPlaylistSubmit');
    if (editPlaylistSubmit) {
        editPlaylistSubmit.addEventListener('click', function() {
            const playlistId = document.getElementById('editPlaylistId').value;
            const name = document.getElementById('editPlaylistName').value.trim();
            const description = document.getElementById('editPlaylistDescription').value.trim();
            
            if (!name) {
                alert('Playlist name is required');
                return;
            }
            
            editPlaylistSubmit.disabled = true;
            
            fetch(`/music/playlists/${playlistId}/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, description: description || null })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error updating playlist: ' + data.error);
                    editPlaylistSubmit.disabled = false;
                    return;
                }
                
                // Reload page
                window.location.reload();
            })
            .catch(error => {
                console.error('Error updating playlist:', error);
                alert('Error updating playlist. Please try again.');
                editPlaylistSubmit.disabled = false;
            });
        });
    }
    
    // Delete playlist
    const deletePlaylistBtns = document.querySelectorAll('.playlist-delete-btn');
    
    deletePlaylistBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const playlistId = this.dataset.playlistId;
            const playlistName = this.dataset.playlistName;
            
            if (!confirm(`Are you sure you want to delete "${playlistName}"? This action cannot be undone.`)) {
                return;
            }
            
            fetch(`/music/playlists/${playlistId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error deleting playlist: ' + data.error);
                    return;
                }
                
                // Reload page
                window.location.reload();
            })
            .catch(error => {
                console.error('Error deleting playlist:', error);
                alert('Error deleting playlist. Please try again.');
            });
        });
    });
    
    // ========== PLAYLIST VIEW PAGE ==========
    
    // Check if we're on the playlist view page
    if (typeof PLAYLIST_ID !== 'undefined') {
        const playlistSongsBody = document.getElementById('playlistSongsBody');
        if (!playlistSongsBody) return;
        
        // Remove song from playlist
        const removeSongBtns = document.querySelectorAll('.remove-song-btn');
        
        removeSongBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const trackUri = this.dataset.trackUri;
                const row = this.closest('tr');
                const songName = row.querySelector('td:nth-child(3) strong').textContent;
                
                if (!confirm(`Remove "${songName}" from this playlist?`)) {
                    return;
                }
                
                fetch(`/music/playlists/${PLAYLIST_ID}/remove-song?track_uri=${encodeURIComponent(trackUri)}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('Error removing song: ' + data.error);
                        return;
                    }
                    
                    // Remove row from table
                    row.remove();
                    
                    // Update row numbers
                    updateRowNumbers();
                    
                    // Show notification
                    showNotification('Song removed from playlist', 'success');
                })
                .catch(error => {
                    console.error('Error removing song:', error);
                    alert('Error removing song. Please try again.');
                });
            });
        });
        
        // Reorder songs - move up
        const moveUpBtns = document.querySelectorAll('.move-up-btn');
        moveUpBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const row = this.closest('tr');
                const prevRow = row.previousElementSibling;
                
                if (!prevRow || !prevRow.classList.contains('playlist-song-row')) {
                    return; // Can't move up
                }
                
                // Swap rows
                playlistSongsBody.insertBefore(row, prevRow);
                updateRowNumbers();
                savePlaylistOrder();
            });
        });
        
        // Reorder songs - move down
        const moveDownBtns = document.querySelectorAll('.move-down-btn');
        moveDownBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const row = this.closest('tr');
                const nextRow = row.nextElementSibling;
                
                if (!nextRow || !nextRow.classList.contains('playlist-song-row')) {
                    return; // Can't move down
                }
                
                // Swap rows
                playlistSongsBody.insertBefore(nextRow, row);
                updateRowNumbers();
                savePlaylistOrder();
            });
        });
        
        // Update row numbers
        function updateRowNumbers() {
            const rows = playlistSongsBody.querySelectorAll('.playlist-song-row');
            rows.forEach((row, index) => {
                const numberCell = row.querySelector('td:first-child');
                if (numberCell) {
                    numberCell.textContent = index + 1;
                }
            });
        }
        
        // Save playlist order
        function savePlaylistOrder() {
            const rows = playlistSongsBody.querySelectorAll('.playlist-song-row');
            const trackUris = Array.from(rows).map(row => row.dataset.trackUri);
            
            fetch(`/music/playlists/${PLAYLIST_ID}/reorder`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ track_uris: trackUris })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error saving order:', data.error);
                    // Don't show alert, just log - order is visual only
                }
            })
            .catch(error => {
                console.error('Error saving playlist order:', error);
            });
        }
    }
    
    // ========== SPOTIFY INTEGRATION ==========
    
    // Check Spotify connection status
    const spotifyStatusIndicator = document.getElementById('spotify-status-indicator');
    const spotifyConnectBtn = document.getElementById('spotify-connect-btn');
    const spotifyDisconnectBtn = document.getElementById('spotify-disconnect-btn');
    const importFromSpotifyBtn = document.getElementById('import-from-spotify-btn');
    
    function checkSpotifyStatus() {
        fetch('/music/spotify/status')
            .then(response => response.json())
            .then(data => {
                if (data.authenticated && data.is_valid) {
                    if (spotifyStatusIndicator) {
                        spotifyStatusIndicator.textContent = 'Connected';
                        spotifyStatusIndicator.className = 'badge bg-success';
                        spotifyStatusIndicator.style.display = 'inline-block';
                    }
                    if (spotifyConnectBtn) spotifyConnectBtn.style.display = 'none';
                    if (spotifyDisconnectBtn) spotifyDisconnectBtn.style.display = 'inline-block';
                    if (importFromSpotifyBtn) importFromSpotifyBtn.style.display = 'inline-block';
                } else {
                    if (spotifyStatusIndicator) {
                        spotifyStatusIndicator.textContent = 'Not Connected';
                        spotifyStatusIndicator.className = 'badge bg-secondary';
                        spotifyStatusIndicator.style.display = 'inline-block';
                    }
                    if (spotifyConnectBtn) spotifyConnectBtn.style.display = 'inline-block';
                    if (spotifyDisconnectBtn) spotifyDisconnectBtn.style.display = 'none';
                    if (importFromSpotifyBtn) importFromSpotifyBtn.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error checking Spotify status:', error);
                if (spotifyStatusIndicator) {
                    spotifyStatusIndicator.textContent = 'Error';
                    spotifyStatusIndicator.className = 'badge bg-danger';
                }
            });
    }
    
    // Check status on page load
    if (spotifyStatusIndicator || spotifyConnectBtn) {
        checkSpotifyStatus();
    }
    
    // Connect to Spotify
    if (spotifyConnectBtn) {
        spotifyConnectBtn.addEventListener('click', function() {
            window.location.href = '/music/spotify/authorize';
        });
    }
    
    // Disconnect from Spotify
    if (spotifyDisconnectBtn) {
        spotifyDisconnectBtn.addEventListener('click', function() {
            if (!confirm('Are you sure you want to disconnect from Spotify?')) {
                return;
            }
            
            fetch('/music/spotify/disconnect', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error disconnecting: ' + data.error);
                    return;
                }
                showNotification('Disconnected from Spotify', 'success');
                checkSpotifyStatus();
            })
            .catch(error => {
                console.error('Error disconnecting:', error);
                alert('Error disconnecting from Spotify. Please try again.');
            });
        });
    }
    
    // Export playlist to Spotify
    const exportToSpotifyBtn = document.getElementById('export-to-spotify-btn');
    if (exportToSpotifyBtn) {
        exportToSpotifyBtn.addEventListener('click', function() {
            if (!confirm('Export this playlist to Spotify? It will be created as a private playlist.')) {
                return;
            }
            
            exportToSpotifyBtn.disabled = true;
            exportToSpotifyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exporting...';
            
            fetch(`/music/playlists/${PLAYLIST_ID}/export-to-spotify`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ public: false })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error exporting to Spotify: ' + data.error);
                    exportToSpotifyBtn.disabled = false;
                    exportToSpotifyBtn.innerHTML = '<i class="fab fa-spotify"></i> Export to Spotify';
                    return;
                }
                
                showNotification('Playlist exported to Spotify successfully!', 'success');
                // Reload page to show updated status
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            })
            .catch(error => {
                console.error('Error exporting to Spotify:', error);
                alert('Error exporting to Spotify. Please try again.');
                exportToSpotifyBtn.disabled = false;
                exportToSpotifyBtn.innerHTML = '<i class="fab fa-spotify"></i> Export to Spotify';
            });
        });
    }
    
    // Re-sync playlist to Spotify
    const resyncToSpotifyBtn = document.getElementById('resync-to-spotify-btn');
    if (resyncToSpotifyBtn) {
        resyncToSpotifyBtn.addEventListener('click', function() {
            if (!confirm('Re-sync this playlist to Spotify? This will update the existing Spotify playlist.')) {
                return;
            }
            
            resyncToSpotifyBtn.disabled = true;
            resyncToSpotifyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing...';
            
            fetch(`/music/playlists/${PLAYLIST_ID}/export-to-spotify`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ public: false, force: true })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error syncing to Spotify: ' + data.error);
                    resyncToSpotifyBtn.disabled = false;
                    resyncToSpotifyBtn.innerHTML = '<i class="fas fa-sync"></i> Re-sync';
                    return;
                }
                
                showNotification('Playlist synced to Spotify successfully!', 'success');
                // Reload page to show updated status
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            })
            .catch(error => {
                console.error('Error syncing to Spotify:', error);
                alert('Error syncing to Spotify. Please try again.');
                resyncToSpotifyBtn.disabled = false;
                resyncToSpotifyBtn.innerHTML = '<i class="fas fa-sync"></i> Re-sync';
            });
        });
    }
    
    // Import from Spotify modal
    const importSpotifyModal = document.getElementById('importSpotifyModal');
    const spotifyPlaylistsLoading = document.getElementById('spotify-playlists-loading');
    const spotifyPlaylistsList = document.getElementById('spotify-playlists-list');
    const spotifyPlaylistsContainer = document.getElementById('spotify-playlists-container');
    const spotifyPlaylistsError = document.getElementById('spotify-playlists-error');
    const spotifyPlaylistsErrorMessage = document.getElementById('spotify-playlists-error-message');
    
    if (importFromSpotifyBtn) {
        importFromSpotifyBtn.addEventListener('click', function() {
            // Show loading
            spotifyPlaylistsLoading.style.display = 'block';
            spotifyPlaylistsList.style.display = 'none';
            spotifyPlaylistsError.style.display = 'none';
            spotifyPlaylistsContainer.innerHTML = '';
            
            // Show modal
            const modal = new bootstrap.Modal(importSpotifyModal);
            modal.show();
            
            // Load playlists
            loadSpotifyPlaylists();
        });
    }
    
    function loadSpotifyPlaylists() {
        fetch('/music/spotify/playlists?limit=50')
            .then(response => response.json())
            .then(data => {
                spotifyPlaylistsLoading.style.display = 'none';
                
                if (data.error) {
                    spotifyPlaylistsError.style.display = 'block';
                    spotifyPlaylistsErrorMessage.textContent = data.error;
                    return;
                }
                
                const playlists = data.playlists || [];
                if (playlists.length === 0) {
                    spotifyPlaylistsContainer.innerHTML = '<div class="alert alert-info">No playlists found in your Spotify account.</div>';
                    spotifyPlaylistsList.style.display = 'block';
                    return;
                }
                
                // Render playlists
                playlists.forEach(playlist => {
                    const item = document.createElement('div');
                    item.className = 'list-group-item list-group-item-action';
                    item.innerHTML = `
                        <div class="d-flex w-100 justify-content-between">
                            <div>
                                <h6 class="mb-1">${escapeHtml(playlist.name)}</h6>
                                ${playlist.description ? `<p class="mb-1 text-muted small">${escapeHtml(playlist.description)}</p>` : ''}
                                <small class="text-muted">${playlist.tracks?.total || 0} tracks</small>
                            </div>
                            <button class="btn btn-sm btn-primary import-playlist-btn" data-spotify-id="${playlist.id}" data-playlist-name="${escapeHtml(playlist.name)}">
                                Import
                            </button>
                        </div>
                    `;
                    spotifyPlaylistsContainer.appendChild(item);
                });
                
                spotifyPlaylistsList.style.display = 'block';
                
                // Add click handlers for import buttons
                document.querySelectorAll('.import-playlist-btn').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const spotifyId = this.dataset.spotifyId;
                        const playlistName = this.dataset.playlistName;
                        
                        if (!confirm(`Import "${playlistName}" from Spotify?`)) {
                            return;
                        }
                        
                        this.disabled = true;
                        this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Importing...';
                        
                        fetch(`/music/spotify/playlists/${spotifyId}/import`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ name: playlistName })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.error) {
                                alert('Error importing playlist: ' + data.error);
                                this.disabled = false;
                                this.innerHTML = 'Import';
                                return;
                            }
                            
                            showNotification(`Imported "${playlistName}" (${data.added_count} tracks added, ${data.skipped_count} skipped)`, 'success');
                            // Close modal and reload page
                            bootstrap.Modal.getInstance(importSpotifyModal).hide();
                            setTimeout(() => {
                                window.location.reload();
                            }, 1000);
                        })
                        .catch(error => {
                            console.error('Error importing playlist:', error);
                            alert('Error importing playlist. Please try again.');
                            this.disabled = false;
                            this.innerHTML = 'Import';
                        });
                    });
                });
            })
            .catch(error => {
                console.error('Error loading Spotify playlists:', error);
                spotifyPlaylistsLoading.style.display = 'none';
                spotifyPlaylistsError.style.display = 'block';
                spotifyPlaylistsErrorMessage.textContent = 'Error loading playlists. Please try again.';
            });
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Notification helper
    function showNotification(message, type = 'info') {
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
});

