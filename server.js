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

// YouTube Download Endpoint - IMPROVED VERSION
app.get('/download/youtube', async (req, res) => {
    try {
        let videoUrl = req.query.url;
        
        if (!videoUrl) {
            return res.status(400).json({ error: 'URL is required' });
        }

        // Clean the URL - remove extra parameters that might cause issues
        videoUrl = cleanYouTubeUrl(videoUrl);
        
        console.log('Processing URL:', videoUrl);
        
        if (!ytdl.validateURL(videoUrl)) {
            return res.status(400).json({ 
                error: 'Invalid YouTube URL',
                details: 'Please make sure you copied a valid YouTube video URL'
            });
        }
        
        const info = await ytdl.getInfo(videoUrl);
        const title = info.videoDetails.title.replace(/[^\w\s]/gi, '') || 'youtube_video';
        
        const format = req.query.format || 'mp4';
        let downloadUrl;
        
        if (format === 'mp3') {
            const audioFormat = ytdl.chooseFormat(info.formats, { 
                quality: 'highestaudio',
                filter: 'audioonly'
            });
            
            if (!audioFormat) {
                return res.status(400).json({ error: 'No audio format available for this video' });
            }
            
            downloadUrl = audioFormat.url;
            res.json({
                success: true,
                title: title,
                downloadUrl: downloadUrl,
                filename: `${title}.mp3`,
                type: 'audio'
            });
        } else {
            const videoFormat = ytdl.chooseFormat(info.formats, { 
                quality: 'highest'
            });
            
            if (!videoFormat) {
                return res.status(400).json({ error: 'No video format available for this video' });
            }
            
            downloadUrl = videoFormat.url;
            res.json({
                success: true,
                title: title,
                downloadUrl: downloadUrl,
                filename: `${title}.mp4`,
                type: 'video'
            });
        }
        
    } catch (error) {
        console.error('YouTube download error:', error);
        res.status(500).json({ 
            error: 'Failed to process YouTube video',
            details: 'This might be due to video restrictions, region blocking, or invalid URL',
            technical: error.message 
        });
    }
});

// Function to clean YouTube URLs
function cleanYouTubeUrl(url) {
    try {
        // Extract just the video ID and create a clean URL
        const videoId = ytdl.getURLVideoID(url);
        return `https://www.youtube.com/watch?v=${videoId}`;
    } catch (error) {
        // If extraction fails, return original URL
        return url;
    }
}

// TikTok Download Endpoint
app.get('/download/tiktok', async (req, res) => {
    try {
        const tiktokUrl = req.query.url;
        
        if (!tiktokUrl) {
            return res.status(400).json({ error: 'URL is required' });
        }
        
        const response = await axios.get(`https://www.tikwm.com/api/?url=${encodeURIComponent(tiktokUrl)}`);
        const data = response.data;
        
        if (data.code !== 0) {
            return res.status(400).json({ error: 'Failed to fetch TikTok video' });
        }
        
        res.json({
            success: true,
            title: data.data?.title || 'TikTok Video',
            downloadUrl: data.data.play,
            filename: `tiktok_video.mp4`,
            type: 'video'
        });
        
    } catch (error) {
        console.error('TikTok download error:', error);
        res.status(500).json({ 
            error: 'Failed to process TikTok video',
            details: error.message 
        });
    }
});

// Universal Download Endpoint
app.get('/download', async (req, res) => {
    const url = req.query.url;
    const format = req.query.format || 'mp4';
    
    if (!url) {
        return res.status(400).json({ error: 'URL is required' });
    }
    
    try {
        if (url.includes('youtube.com') || url.includes('youtu.be')) {
            const response = await axios.get(`http://localhost:${PORT}/download/youtube?url=${encodeURIComponent(url)}&format=${format}`);
            res.json(response.data);
        } else if (url.includes('tiktok.com')) {
            const response = await axios.get(`http://localhost:${PORT}/download/tiktok?url=${encodeURIComponent(url)}`);
            res.json(response.data);
        } else {
            res.status(400).json({ error: 'Unsupported platform. Try YouTube or TikTok.' });
        }
    } catch (error) {
        res.status(500).json({ 
            error: 'Download failed',
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
