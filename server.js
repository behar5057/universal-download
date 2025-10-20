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

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'OK', message: 'Universal Download Backend is running!' });
});

app.listen(PORT, () => {
    console.log(`🚀 Universal Download Backend running on port ${PORT}`);
    console.log(`📱 Access your site: http://localhost:${PORT}`);
});
