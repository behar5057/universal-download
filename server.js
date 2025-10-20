const express = require('express');
const cors = require('cors');
const ytdl = require('ytdl-core');
const axios = require('axios');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('.'));

// Serve the main page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// YouTube Download Endpoint - FIXED VERSION
app.get('/download/youtube', async (req, res) => {
    try {
        let videoUrl = req.query.url;
        
        console.log('Received URL:', videoUrl);
        
        if (!videoUrl) {
            return res.status(400).json({ error: 'URL is required' });
        }

        // Clean the URL - extract only the video ID
        const cleanUrl = extractCleanYouTubeUrl(videoUrl);
        console.log('Cleaned URL:', cleanUrl);
        
        if (!cleanUrl) {
            return res.status(400).json({ 
                error: 'Invalid YouTube URL',
                details: 'Could not extract video ID from the URL'
            });
        }
        
        if (!ytdl.validateURL(cleanUrl)) {
            return res.status(400).json({ 
                error: 'Invalid YouTube URL',
                details: 'Please use a standard YouTube video URL'
            });
        }
        
        const info = await ytdl.getInfo(cleanUrl);
        const title = info.videoDetails.title.replace(/[^\w\s\-]/gi, '') || 'youtube_video';
        
        const format = req.query.format || 'mp4';
        let downloadUrl;
        
        if (format === 'mp3') {
            const audioFormats = ytdl.filterFormats(info.formats, 'audioonly');
            const audioFormat = ytdl.chooseFormat(audioFormats, { 
                quality: 'highestaudio'
            });
            
            if (!audioFormat) {
                return res.status(400).json({ error: 'No audio format available for this video' });
            }
            
            downloadUrl = audioFormat.url;
            res.json({
                success: true,
                title: title,
                downloadUrl: downloadUrl,
                filename: `${title.substring(0, 50)}.mp3`,
                type: 'audio'
            });
        } else {
            const videoFormats = ytdl.filterFormats(info.formats, 'videoonly');
            const videoFormat = ytdl.chooseFormat(videoFormats, { 
                quality: 'highest'
            });
            
            if (!videoFormat) {
                // Fallback to any format
                const anyFormat = ytdl.chooseFormat(info.formats, { quality: 'highest' });
                if (!anyFormat) {
                    return res.status(400).json({ error: 'No video format available for this video' });
                }
                downloadUrl = anyFormat.url;
            } else {
                downloadUrl = videoFormat.url;
            }
            
            res.json({
                success: true,
                title: title,
                downloadUrl: downloadUrl,
                filename: `${title.substring(0, 50)}.mp4`,
                type: 'video'
            });
        }
        
    } catch (error) {
        console.error('YouTube download error:', error);
        res.status(500).json({ 
            error: 'Failed to process YouTube video',
            details: 'This video might be restricted or unavailable',
            technical: error.message 
        });
    }
});

// Function to extract clean YouTube URL
function extractCleanYouTubeUrl(url) {
    try {
        // Try to extract video ID using ytdl-core
        const videoId = ytdl.getURLVideoID(url);
        if (videoId) {
            return `https://www.youtube.com/watch?v=${videoId}`;
        }
    } catch (error) {
        console.log('ytdl-core extraction failed, trying manual extraction');
    }
    
    // Manual extraction as fallback
    const patterns = [
        /(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&]+)/,
        /youtube\.com\/watch\?.*v=([^&]+)/,
        /youtu\.be\/([^?]+)/
    ];
    
    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match && match[1]) {
            return `https://www.youtube.com/watch?v=${match[1]}`;
        }
    }
    
    return null;
}

// Simple YouTube test endpoint
app.get('/download/simple', async (req, res) => {
    try {
        const videoUrl = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'; // Rick Astley - Never Gonna Give You Up
        const info = await ytdl.getInfo(videoUrl);
        const title = info.videoDetails.title;
        
        const format = ytdl.chooseFormat(info.formats, { quality: 'highest' });
        
        res.json({
            success: true,
            title: title,
            downloadUrl: format.url,
            filename: `${title}.mp4`,
            type: 'video',
            message: 'This is a test video to verify the download works'
        });
        
    } catch (error) {
        res.status(500).json({ 
            error: 'Test failed',
            details: error.message 
        });
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ 
        status: 'OK', 
        message: 'Universal Download Backend is running!',
        timestamp: new Date().toISOString()
    });
});

app.listen(PORT, () => {
    console.log(`🚀 Universal Download Backend running on port ${PORT}`);
    console.log(`📱 Access your site: http://localhost:${PORT}`);
});
