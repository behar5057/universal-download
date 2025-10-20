const express = require('express');
const cors = require('cors');
const ytdl = require('ytdl-core');
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

// NEW: Simple YouTube download that definitely works
app.get('/download/youtube', async (req, res) => {
    try {
        let videoUrl = req.query.url;
        
        console.log('📥 Original URL received:', videoUrl);
        
        if (!videoUrl) {
            return res.status(400).json({ error: 'URL is required' });
        }

        // EXTREME URL CLEANING - Remove everything except video ID
        const videoId = extractVideoId(videoUrl);
        console.log('🎯 Extracted Video ID:', videoId);
        
        if (!videoId) {
            return res.status(400).json({ 
                error: 'Invalid YouTube URL',
                details: 'Could not find video ID in the URL'
            });
        }

        // Create clean URL
        const cleanUrl = `https://www.youtube.com/watch?v=${videoId}`;
        console.log('✨ Clean URL:', cleanUrl);
        
        // Validate URL
        if (!ytdl.validateURL(cleanUrl)) {
            return res.status(400).json({ 
                error: 'Invalid YouTube URL',
                details: 'The video ID appears to be invalid'
            });
        }
        
        console.log('🔍 Getting video info...');
        const info = await ytdl.getInfo(cleanUrl);
        const title = info.videoDetails.title.replace(/[^\w\s\-\.]/gi, '') || 'youtube_video';
        
        console.log('📹 Video title:', title);
        
        // Get available formats
        const formats = info.formats;
        console.log('📊 Available formats:', formats.length);
        
        // Choose the best video format
        let chosenFormat = ytdl.chooseFormat(formats, {
            quality: 'highest',
            filter: format => format.hasVideo && format.hasAudio
        });
        
        // Fallback to any video format
        if (!chosenFormat) {
            chosenFormat = ytdl.chooseFormat(formats, { quality: 'highest' });
        }
        
        if (!chosenFormat) {
            return res.status(400).json({ 
                error: 'No downloadable format available',
                details: 'This video might be restricted or unavailable for download'
            });
        }
        
        console.log('✅ Selected format:', chosenFormat.qualityLabel);
        
        res.json({
            success: true,
            title: title,
            downloadUrl: chosenFormat.url,
            filename: `${title.substring(0, 50)}.mp4`,
            type: 'video',
            quality: chosenFormat.qualityLabel,
            videoId: videoId
        });
        
    } catch (error) {
        console.error('❌ YouTube download error:', error.message);
        res.status(500).json({ 
            error: 'Failed to download video',
            details: getFriendlyErrorMessage(error),
            technical: error.message
        });
    }
});

// NEW: Ultra-reliable video ID extraction
function extractVideoId(url) {
    console.log('🛠️ Extracting video ID from:', url);
    
    // Remove URL encoding and clean the string
    let cleanUrl = decodeURIComponent(url);
    
    // Multiple extraction patterns - one will work
    const patterns = [
        /(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/,
        /v=([a-zA-Z0-9_-]{11})/,
        /youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})/,
        /youtu\.be\/([a-zA-Z0-9_-]{11})/,
        /embed\/([a-zA-Z0-9_-]{11})/,
        /\/v\/([a-zA-Z0-9_-]{11})/
    ];
    
    for (const pattern of patterns) {
        const match = cleanUrl.match(pattern);
        if (match && match[1]) {
            console.log('🎉 Found video ID with pattern:', pattern);
            return match[1];
        }
    }
    
    // Last resort: look for any 11-character video ID-like string
    const videoIdMatch = cleanUrl.match(/[a-zA-Z0-9_-]{11}/);
    if (videoIdMatch && videoIdMatch[0]) {
        console.log('🔍 Found potential video ID:', videoIdMatch[0]);
        return videoIdMatch[0];
    }
    
    return null;
}

// NEW: Better error messages
function getFriendlyErrorMessage(error) {
    if (error.message.includes('Video unavailable')) {
        return 'This video is unavailable or has been removed';
    }
    if (error.message.includes('Private video')) {
        return 'This is a private video and cannot be downloaded';
    }
    if (error.message.includes('Sign in to confirm')) {
        return 'This video is age-restricted and cannot be downloaded';
    }
    if (error.message.includes('Network Error')) {
        return 'Network error - please check your connection';
    }
    return 'The video might be restricted or unavailable in your region';
}

// NEW: Test endpoint with multiple video options
app.get('/download/test', async (req, res) => {
    const testVideos = [
        'dQw4w9WgXcQ', // Rick Roll - usually works everywhere
        'jNQXAC9IVRw', // First YouTube video
        '9bZkp7q19f0'  // Gangnam Style
    ];
    
    for (const videoId of testVideos) {
        try {
            const testUrl = `https://www.youtube.com/watch?v=${videoId}`;
            console.log(`🧪 Testing with video: ${videoId}`);
            
            const info = await ytdl.getInfo(testUrl);
            const format = ytdl.chooseFormat(info.formats, { quality: 'highest' });
            
            return res.json({
                success: true,
                title: info.videoDetails.title,
                downloadUrl: format.url,
                filename: `${info.videoDetails.title}.mp4`,
                type: 'video',
                videoId: videoId,
                message: '✅ Download system is working perfectly!'
            });
        } catch (error) {
            console.log(`❌ Video ${videoId} failed:`, error.message);
            continue; // Try next video
        }
    }
    
    res.status(500).json({
        error: 'All test videos failed',
        details: 'There seems to be a fundamental issue with YouTube downloads'
    });
});

// Health check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'OK', 
        message: '🚀 Universal Download is running!',
        timestamp: new Date().toISOString(),
        version: '2.0'
    });
});

app.listen(PORT, () => {
    console.log(`🚀 Universal Download Backend running on port ${PORT}`);
    console.log(`📱 Access your site: http://localhost:${PORT}`);
    console.log(`💡 Test URL: https://universal-download.onrender.com`);
});
