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

