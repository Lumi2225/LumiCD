document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const audio = document.getElementById('audio-player');
    const playBtn = document.getElementById('play-btn');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const ejectBtn = document.getElementById('eject-btn');
    const volumeSlider = document.getElementById('volume-slider');
    const progressBar = document.getElementById('progress-bar');
    const progressContainer = document.getElementById('progress-container');
    const currentTimeEl = document.getElementById('current-time');
    const totalTimeEl = document.getElementById('total-time');
    const albumArt = document.getElementById('album-art');
    const trackTitle = document.getElementById('track-title');
    const artistName = document.getElementById('artist-name');
    const albumName = document.getElementById('album-name');
    const playerEl = document.getElementById('player');
    const noCdEl = document.getElementById('no-cd');
    const trackListEl = document.getElementById('track-list');
    const glow = document.getElementById('glow');

    let isPlaying = false;
    let currentTrackData = null;

    // Socket.io Events
    socket.on('status', (state) => {
        updateUI(state);
    });

    socket.on('track_change', (state) => {
        if (isPlaying) {
            startStreaming();
        }
    });

    function updateUI(state) {
        if (!state.cd_inserted) {
            playerEl.classList.add('hidden');
            noCdEl.classList.remove('hidden');
            isPlaying = false;
            audio.pause();
            return;
        }

        playerEl.classList.remove('hidden');
        noCdEl.classList.add('hidden');

        isPlaying = state.playing;

        // Update Metadata
        if (state.metadata) {
            const track = state.metadata.tracks.find(t => t.number === state.current_track);
            trackTitle.innerText = track ? track.title : `Track ${state.current_track}`;
            artistName.innerText = state.metadata.artist;
            albumName.innerText = state.metadata.album;
            if (state.metadata.cover) {
                albumArt.src = state.metadata.cover;
            }

            if (track && track.duration) {
                totalTimeEl.innerText = formatTime(track.duration);
                const percent = (state.elapsed / track.duration) * 100;
                progressBar.style.width = `${Math.min(percent, 100)}%`;
                currentTimeEl.innerText = formatTime(state.elapsed);
            }

            renderTrackList(state.metadata.tracks, state.current_track);
        }

        // Update Play/Pause Button
        playBtn.innerHTML = isPlaying ? '<i class="fas fa-pause"></i>' : '<i class="fas fa-play ml-1"></i>';

        if (isPlaying) {
            document.body.classList.add('playing');
            glow.style.backgroundColor = 'rgba(59, 130, 246, 0.3)';
        } else {
            document.body.classList.remove('playing');
            glow.style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
        }
    }

    function formatTime(seconds) {
        if (!seconds) return "00:00";
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    function renderTrackList(tracks, currentTrackNum) {
        if (!tracks || tracks.length === 0) return;
        trackListEl.classList.remove('hidden');

        // Only re-render if track count changed or first time
        if (trackListEl.children.length !== tracks.length) {
            trackListEl.innerHTML = '';
            tracks.forEach(track => {
                const div = document.createElement('div');
                div.className = `flex items-center justify-between p-3 rounded-xl cursor-pointer transition-colors hover:bg-white/5 ${track.number === currentTrackNum ? 'bg-white/10 text-blue-400' : 'text-white/60'}`;
                div.innerHTML = `
                    <div class="flex items-center gap-4">
                        <span class="w-6 text-sm font-mono opacity-50">${track.number}</span>
                        <span class="font-medium">${track.title}</span>
                    </div>
                    <span class="text-sm font-mono opacity-50">${formatTime(track.duration)}</span>
                `;
                div.onclick = () => {
                    // Logic to jump to track could be added here
                    // For now we just use next/prev as specified
                };
                trackListEl.appendChild(div);
            });
        } else {
            // Update active state
            Array.from(trackListEl.children).forEach((child, index) => {
                const track = tracks[index];
                if (track.number === currentTrackNum) {
                    child.classList.add('bg-white/10', 'text-blue-400');
                    child.classList.remove('text-white/60');
                } else {
                    child.classList.remove('bg-white/10', 'text-blue-400');
                    child.classList.add('text-white/60');
                }
            });
        }
    }

    function startStreaming() {
        // Detect iPhone/Safari for MP3 fallback
        const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
        const isIOS = /iPad|iPhone|iPod/.test(navigator.platform) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

        const streamUrl = (isSafari || isIOS) ? '/stream.mp3' : '/stream';
        audio.src = `${streamUrl}?t=${Date.now()}`; // Cache busting
        audio.play().catch(e => console.error("Playback failed:", e));
    }

    // Control Handlers
    playBtn.addEventListener('click', () => {
        if (isPlaying) {
            fetch('/pause').then(() => {
                audio.pause();
            });
        } else {
            fetch('/play').then(() => {
                if (audio.src.includes('/stream')) {
                    audio.play();
                } else {
                    startStreaming();
                }
            });
        }
    });

    nextBtn.addEventListener('click', () => {
        fetch('/next');
    });

    prevBtn.addEventListener('click', () => {
        fetch('/previous');
    });

    ejectBtn.addEventListener('click', () => {
        fetch('/eject');
    });

    volumeSlider.addEventListener('input', (e) => {
        audio.volume = e.target.value / 100;
    });

    // Initialize Volume
    audio.volume = volumeSlider.value / 100;

    // Handle end of track (automatic next)
    audio.addEventListener('ended', () => {
        fetch('/next');
    });
});
