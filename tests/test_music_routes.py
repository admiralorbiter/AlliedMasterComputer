import pytest
import os
import tempfile
import csv
from flask import url_for
from flask_app.models import Song, MusicImportJob, db
from flask_app.utils.music_importer import import_csv_file


class TestMusicLibraryRoutes:
    """Test music library routes functionality"""
    
    def test_music_library_requires_login(self, client):
        """Test that music library page requires login"""
        response = client.get('/music/library')
        # Should redirect to login
        assert response.status_code in [302, 401]
    
    def test_music_library_page(self, client, test_user, app):
        """Test music library page loads"""
        with app.app_context():
            # Create a test song
            song = Song(
                track_uri='spotify:track:test123',
                track_name='Test Song',
                artist_names='Test Artist',
                album_name='Test Album',
                popularity=50
            )
            db.session.add(song)
            db.session.commit()
        
        # Login
        client.post('/login', data={
            'username': test_user.username,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        response = client.get('/music/library')
        assert response.status_code == 200
        assert b'Music Library' in response.data
        assert b'Test Song' in response.data
    
    def test_music_library_search(self, client, test_user, app):
        """Test music library search functionality"""
        with app.app_context():
            # Create test songs
            song1 = Song(
                track_uri='spotify:track:test1',
                track_name='Rock Song',
                artist_names='Rock Artist',
                album_name='Rock Album',
                popularity=70
            )
            song2 = Song(
                track_uri='spotify:track:test2',
                track_name='Jazz Song',
                artist_names='Jazz Artist',
                album_name='Jazz Album',
                popularity=60
            )
            db.session.add_all([song1, song2])
            db.session.commit()
        
        # Login
        client.post('/login', data={
            'username': test_user.username,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        # Search for rock
        response = client.get('/music/library?q=Rock')
        assert response.status_code == 200
        assert b'Rock Song' in response.data
        assert b'Jazz Song' not in response.data
    
    def test_music_library_filters(self, client, test_user, app):
        """Test music library filters"""
        with app.app_context():
            # Create test songs with different explicit values
            song1 = Song(
                track_uri='spotify:track:test1',
                track_name='Explicit Song',
                artist_names='Artist',
                explicit=True,
                popularity=50
            )
            song2 = Song(
                track_uri='spotify:track:test2',
                track_name='Clean Song',
                artist_names='Artist',
                explicit=False,
                popularity=50
            )
            db.session.add_all([song1, song2])
            db.session.commit()
        
        # Login
        client.post('/login', data={
            'username': test_user.username,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        # Filter for explicit only
        response = client.get('/music/library?explicit=true')
        assert response.status_code == 200
        assert b'Explicit Song' in response.data
        assert b'Clean Song' not in response.data
        
        # Filter for clean only
        response = client.get('/music/library?explicit=false')
        assert response.status_code == 200
        assert b'Clean Song' in response.data
        assert b'Explicit Song' not in response.data
    
    def test_music_library_pagination(self, client, test_user, app):
        """Test music library pagination"""
        with app.app_context():
            # Create multiple songs
            songs = []
            for i in range(25):
                song = Song(
                    track_uri=f'spotify:track:test{i}',
                    track_name=f'Song {i}',
                    artist_names='Artist',
                    popularity=50
                )
                songs.append(song)
            db.session.add_all(songs)
            db.session.commit()
        
        # Login
        client.post('/login', data={
            'username': test_user.username,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        # Check first page
        response = client.get('/music/library?page=1')
        assert response.status_code == 200
        assert b'Song 0' in response.data
        
        # Check second page
        response = client.get('/music/library?page=2')
        assert response.status_code == 200


class TestMusicSongDetails:
    """Test song details endpoint"""
    
    def test_song_details_requires_login(self, client):
        """Test that song details requires login"""
        response = client.get('/music/library/song?track_uri=test')
        assert response.status_code in [302, 401]
    
    def test_song_details_success(self, client, test_user, app):
        """Test getting song details"""
        with app.app_context():
            song = Song(
                track_uri='spotify:track:test123',
                track_name='Test Song',
                artist_names='Test Artist',
                album_name='Test Album',
                popularity=75,
                tempo=120.5,
                explicit=True
            )
            db.session.add(song)
            db.session.commit()
        
        # Login
        client.post('/login', data={
            'username': test_user.username,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        response = client.get('/music/library/song?track_uri=spotify:track:test123')
        assert response.status_code == 200
        data = response.get_json()
        assert data['track_uri'] == 'spotify:track:test123'
        assert data['track_name'] == 'Test Song'
        assert data['popularity'] == 75
        assert data['tempo'] == 120.5
        assert data['explicit'] is True
    
    def test_song_details_not_found(self, client, test_user):
        """Test song details for non-existent song"""
        # Login
        client.post('/login', data={
            'username': test_user.username,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        response = client.get('/music/library/song?track_uri=spotify:track:nonexistent')
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_song_details_missing_param(self, client, test_user):
        """Test song details without track_uri parameter"""
        # Login
        client.post('/login', data={
            'username': test_user.username,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        response = client.get('/music/library/song')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestMusicImport:
    """Test music import functionality"""
    
    def test_import_requires_login(self, client):
        """Test that import requires login"""
        response = client.post('/music/library/import')
        assert response.status_code in [302, 401]
    
    def test_import_no_file(self, client, test_user):
        """Test import without file"""
        # Login
        client.post('/login', data={
            'username': test_user.username,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        response = client.post('/music/library/import')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_import_invalid_file_type(self, client, test_user):
        """Test import with non-CSV file"""
        # Login
        client.post('/login', data={
            'username': test_user.username,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('test content')
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as file:
                response = client.post('/music/library/import', 
                                      data={'csv_file': (file, 'test.txt')},
                                      content_type='multipart/form-data')
                assert response.status_code == 400
                data = response.get_json()
                assert 'error' in data
        finally:
            os.unlink(temp_path)
    
    def test_import_status_requires_login(self, client):
        """Test that import status requires login"""
        response = client.get('/music/library/import-status?job_id=test')
        assert response.status_code in [302, 401]
    
    def test_import_status_not_found(self, client, test_user):
        """Test import status for non-existent job"""
        # Login
        client.post('/login', data={
            'username': test_user.username,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        response = client.get('/music/library/import-status?job_id=nonexistent')
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_import_status_missing_param(self, client, test_user):
        """Test import status without job_id"""
        # Login
        client.post('/login', data={
            'username': test_user.username,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        response = client.get('/music/library/import-status')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestMusicImportDeduplication:
    """Test that import properly deduplicates by track_uri"""
    
    def test_import_deduplicates(self, client, test_user, app):
        """Test that importing the same track_uri twice only creates one record"""
        with app.app_context():
            # Create a CSV file with duplicate track URIs
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'Track URI', 'Track Name', 'Album Name', 'Artist Name(s)',
                    'Release Date', 'Duration (ms)', 'Popularity', 'Explicit'
                ])
                writer.writeheader()
                writer.writerow({
                    'Track URI': 'spotify:track:duplicate',
                    'Track Name': 'First Import',
                    'Album Name': 'Album',
                    'Artist Name(s)': 'Artist',
                    'Release Date': '2020-01-01',
                    'Duration (ms)': '200000',
                    'Popularity': '50',
                    'Explicit': 'false'
                })
                writer.writerow({
                    'Track URI': 'spotify:track:duplicate',
                    'Track Name': 'Second Import',
                    'Album Name': 'Album',
                    'Artist Name(s)': 'Artist',
                    'Release Date': '2020-01-01',
                    'Duration (ms)': '200000',
                    'Popularity': '50',
                    'Explicit': 'false'
                })
                temp_path = f.name
            
            try:
                # Import the CSV
                import_csv_file('test-job-id', temp_path, app)
                
                # Check that only one song was created
                songs = Song.query.filter_by(track_uri='spotify:track:duplicate').all()
                assert len(songs) == 1
                
                # Check that the first import's data was kept
                assert songs[0].track_name == 'First Import'
                
                # Check import job stats
                job = MusicImportJob.find_by_id('test-job-id')
                if job:
                    assert job.inserted_count == 1
                    assert job.duplicate_count == 1
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                
                # Clean up
                Song.query.filter_by(track_uri='spotify:track:duplicate').delete()
                MusicImportJob.query.filter_by(id='test-job-id').delete()
                db.session.commit()

