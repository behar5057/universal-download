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
app.use(express.static('.')); // Serve frontend files

// Serve the main page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// YouTube Download Endpoint
app.get('/download/youtube', async (req, res) => {
    try {
        const videoUrl = req.query.url;
        const format = req.query.format || 'mp4';
        
        if (!videoUrl) {
            return res.status(400).json({ error: 'URL is required' });
        }
        
        if (!ytdl.validateURL(videoUrl)) {
            return res.status(400).json({ error: 'Invalid YouTube URL' });
        }
        
        const info = await ytdl.getInfo(videoUrl);
        const title = info.videoDetails.title.replace(/[^\w\s]/gi, '');
        
        let downloadUrl;
        
        if (format === 'mp3') {
            // For audio - we'll return the download URL
            const audioFormat = ytdl.chooseFormat(info.formats, { 
                quality: 'highestaudio',
                filter: 'audioonly'
            });
            downloadUrl = audioFormat.url;
            res.json({
                success: true,
                title: title,
                downloadUrl: downloadUrl,
                filename: `${title}.mp3`,
                type: 'audio'
            });
        } else {
            // For video
            const videoFormat = ytdl.chooseFormat(info.formats, { 
                quality: 'highest'
            });
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
            details: error.message 
        });
    }
});

// TikTok Download Endpoint (using public API)
app.get('/download/tiktok', async (req, res) => {
    try {
        const tiktokUrl = req.query.url;
        
        if (!tiktokUrl) {
            return res.status(400).json({ error: 'URL is required' });
        }
        
        // Using TikTok download API
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

// Instagram Download Endpoint
app.get('/download/instagram', async (req, res) => {
    try {
        const instagramUrl = req.query.url;
        
        if (!instagramUrl) {
            return res.status(400).json({ error: 'URL is required' });
        }
        
        // Using Instagram download API
        const response = await axios.get(`https://instagram-downloader-download-instagram-videos-stories.p.rapidapi.com/index`, {
            params: { url: instagramUrl },
            headers: {
                'X-RapidAPI-Key': 'your-rapidapi-key-here', // You'll need to get this
                'X-RapidAPI-Host': 'instagram-downloader-download-instagram-videos-stories.p.rapidapi.com'
            }
        });
        
        const data = response.data;
        res.json({
            success: true,
            title: 'Instagram Media',
            downloadUrl: data.media,
            filename: `instagram_media.mp4`,
            type: 'video'
        });
        
    } catch (error) {
        console.error('Instagram download error:', error);
        res.status(500).json({ 
            error: 'Failed to process Instagram media',
            details: error.message 
        });
    }
});

// Universal Download Endpoint - tries to detect platform
app.get('/download', async (req, res) => {
    const url = req.query.url;
    const format = req.query.format || 'mp4';
    
    if (!url) {
        return res.status(400).json({ error: 'URL is required' });
    }
    
    try {
        if (url.includes('youtube.com') || url.includes('youtu.be')) {
            // Redirect to YouTube endpoint
            const response = await axios.get(`http://localhost:${PORT}/download/youtube?url=${encodeURIComponent(url)}&format=${format}`);
            res.json(response.data);
        } else if (url.includes('tiktok.com')) {
            // Redirect to TikTok endpoint
            const response = await axios.get(`http://localhost:${PORT}/download/tiktok?url=${encodeURIComponent(url)}`);
            res.json(response.data);
        } else if (url.includes('instagram.com')) {
            // Redirect to Instagram endpoint
            const response = await axios.get(`http://localhost:${PORT}/download/instagram?url=${encodeURIComponent(url)}`);
            res.json(response.data);
        } else {
            res.status(400).json({ error: 'Unsupported platform. Try YouTube, TikTok, or Instagram.' });
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
    res.json({ status: 'OK', message: 'Universal Download Backend is running!' });
});

app.listen(PORT, () => {
    console.log(`🚀 Universal Download Backend running on port ${PORT}`);
    console.log(`📱 Access your site: http://localhost:${PORT}`);
});
