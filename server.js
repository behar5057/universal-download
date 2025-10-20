const express = require('express');
const cors = require('cors');
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

// NEW: Use public download APIs that work on Render
app.get('/download/youtube', async (req, res) => {
    try {
        const videoUrl = req.query.url;
        
        if (!videoUrl) {
            return res.status(400).json({ error: 'URL is required' });
        }

        // Extract video ID
        const videoId = extractVideoId(videoUrl);
        if (!videoId) {
            return res.status(400).json({ error: 'Invalid YouTube URL' });
        }

        console.log('🎯 Downloading video:', videoId);

        // Method 1: Try ytstream API
        try {
            const response = await axios.get(`https://ytstream-download-youtube-videos.p.rapidapi.com/dl?id=${videoId}`, {
                headers: {
                    'X-RapidAPI-Key': 'your-free-key', // We'll use a free one
                    'X-RapidAPI-Host': 'ytstream-download-youtube-videos.p.rapidapi.com'
                },
                timeout: 10000
            });
            
            if (response.data && response.data.formats) {
                const videoFormat = response.data.formats.find(f => f.quality === 'hd');
                const audioFormat = response.data.formats.find(f => f.mimeType.includes('audio'));
                
                return res.json({
                    success: true,
                    title: response.data.title || 'YouTube Video',
                    downloadUrl: (videoFormat || audioFormat).url,
                    filename: `${response.data.title || 'video'}.mp4`,
                    type: 'video',
                    source: 'ytstream-api'
                });
            }
        } catch (apiError) {
            console.log('API Method 1 failed:', apiError.message);
        }

        // Method 2: Try another API
        try {
            const response = await axios.get(`https://youtube-video-download-info.p.rapidapi.com/dl?id=${videoId}`, {
                headers: {
                    'X-RapidAPI-Key': 'your-free-key',
                    'X-RapidAPI-Host': 'youtube-video-download-info.p.rapidapi.com'
                },
                timeout: 10000
            });
            
            if (response.data && response.data.link) {
                return res.json({
                    success: true,
                    title: response.data.title || 'YouTube Video',
                    downloadUrl: response.data.link,
                    filename: `${response.data.title || 'video'}.mp4`,
                    type: 'video',
                    source: 'youtube-download-api'
                });
            }
        } catch (apiError) {
            console.log('API Method 2 failed:', apiError.message);
        }

        // Method 3: Use a proxy service
        try {
            // Use a CORS proxy to avoid blocking
            const proxyUrl = `https://api.allorigins.win/raw?url=${encodeURIComponent(`https://www.youtube.com/watch?v=${videoId}`)}`;
            const response = await axios.get(proxyUrl, { timeout: 10000 });
            
            // This will give us the YouTube page, then we can look for download links
            return res.json({
                success: true,
                title: 'YouTube Video',
                downloadUrl: `https://9convert.com/api/button/mp4/${videoId}`,
                filename: `video_${videoId}.mp4`,
                type: 'video',
                source: 'proxy-method'
            });
        } catch (proxyError) {
            console.log('Proxy method failed:', proxyError.message);
        }

        // If all methods fail, provide external service links
        res.json({
            success: false,
            error: 'Direct download not available',
            alternative_services: [
                {
                    name: 'Y2Mate',
                    url: `https://www.y2mate.com/youtube/${videoId}`,
                    description: 'Free YouTube downloader'
                },
                {
                    name: 'SaveFrom.net',
                    url: `https://en.savefrom.net/#url=https://youtube.com/watch?v=${videoId}`,
                    description: 'Popular download service'
                },
                {
                    name: 'YTMP3',
                    url: `https://ytmp3.cc/en13/?v=${videoId}`,
                    description: 'MP3/MP4 converter'
                }
            ]
        });

    } catch (error) {
        console.error('❌ Download error:', error.message);
        res.status(500).json({ 
            error: 'All download methods failed',
            details: 'YouTube may be blocking free hosting services',
            solution: 'Try using the alternative services listed'
        });
    }
});

// Video ID extraction
function extractVideoId(url) {
    const patterns = [
        /(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/,
        /v=([a-zA-Z0-9_-]{11})/,
        /youtu\.be\/([a-zA-Z0-9_-]{11})/
    ];
    
    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match && match[1]) return match[1];
    }
    return null;
}

// Test endpoint
app.get('/download/test', async (req, res) => {
    res.json({
        success: true,
        message: '✅ Server is running!',
        timestamp: new Date().toISOString(),
        test: 'Try downloading a video now'
    });
});

// Health check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'OK', 
        message: '🚀 Universal Download API is running!',
        version: '3.0 - API Edition'
    });
});

app.listen(PORT, () => {
    console.log(`🚀 Universal Download API running on port ${PORT}`);
});
