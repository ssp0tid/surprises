import { getTheme, getAllThemes } from './themes.js';
import { parseAspectRatio, escapeHtml, escapeHtmlAttr } from './utils.js';

export function generateCSS(theme, aspectRatio) {
  const ratio = parseAspectRatio(aspectRatio);
  const vars = theme.vars;

  return `
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
${Object.entries(vars).map(([key, value]) => `  ${key}: ${value};`).join('\n')}
}

html, body {
  height: 100%;
  overflow: hidden;
  font-family: var(--font-body);
  font-weight: var(--body-weight);
  font-size: 16px;
  color: var(--text-primary);
  background: var(--bg-primary);
}

.presentation {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
}

.slides {
  width: ${ratio.width * 10}vh;
  height: ${ratio.height * 10}vh;
  max-width: 100vw;
  max-height: 100vh;
  position: relative;
  overflow: hidden;
}

.slide {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  padding: var(--slide-padding);
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: var(--bg-primary);
  opacity: 0;
  visibility: hidden;
  transition: opacity var(--transition-duration) ease, transform var(--transition-duration) ease;
  transform: translateX(100%);
  overflow: auto;
}

.slide.active {
  opacity: 1;
  visibility: visible;
  transform: translateX(0);
}

.slide.prev {
  transform: translateX(-100%);
}

.slide.fade .slide {
  opacity: 0;
}

.slide.fade .slide.active {
  opacity: 1;
  transform: none;
}

.slide h1 {
  font-family: var(--font-heading);
  font-size: calc(var(--base-size) * var(--heading-scale));
  font-weight: var(--heading-weight);
  line-height: var(--line-height);
  margin-bottom: 0.5em;
  color: var(--text-primary);
}

.slide h2 {
  font-family: var(--font-heading);
  font-size: calc(var(--base-size) * 1.25);
  font-weight: var(--heading-weight);
  line-height: var(--line-height);
  margin-bottom: 0.5em;
  color: var(--text-primary);
}

.slide h3, .slide h4, .slide h5, .slide h6 {
  font-family: var(--font-heading);
  font-size: calc(var(--base-size) * 1);
  font-weight: var(--heading-weight);
  line-height: var(--line-height);
  margin-bottom: 0.5em;
  color: var(--text-primary);
}

.slide p {
  font-size: var(--base-size);
  line-height: var(--line-height);
  margin-bottom: 0.5em;
  color: var(--text-primary);
}

.slide ul, .slide ol {
  font-size: var(--base-size);
  line-height: var(--line-height);
  margin-left: 1.5em;
  margin-bottom: 0.5em;
}

.slide li {
  margin-bottom: 0.25em;
}

.slide code {
  font-family: var(--font-mono);
  background: var(--bg-secondary);
  padding: 0.1em 0.3em;
  border-radius: 3px;
  font-size: 0.9em;
}

.slide pre {
  background: var(--bg-secondary);
  padding: 1em;
  border-radius: 5px;
  overflow: auto;
  margin: 1em 0;
  font-family: var(--font-mono);
  font-size: 0.85em;
  line-height: 1.4;
}

.slide pre code {
  background: none;
  padding: 0;
}

.slide blockquote {
  border-left: 4px solid var(--accent);
  padding-left: 1em;
  margin: 1em 0;
  font-style: italic;
  color: var(--text-secondary);
}

.slide a {
  color: var(--accent);
  text-decoration: none;
}

.slide a:hover {
  text-decoration: underline;
}

.slide img {
  max-width: 100%;
  max-height: 60vh;
  display: block;
  margin: 1em auto;
}

.slide hr {
  border: none;
  border-top: 2px solid var(--accent);
  margin: 1em 0;
}

.controls {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px 20px;
  background: var(--bg-secondary);
  border-radius: 30px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.presentation:hover .controls {
  opacity: 1;
}

.controls button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--text-primary);
  padding: 5px 10px;
  border-radius: 5px;
  transition: background 0.2s ease;
}

.controls button:hover {
  background: var(--accent);
  color: white;
}

.controls button:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.slide-counter {
  font-size: 14px;
  color: var(--text-secondary);
  min-width: 60px;
  text-align: center;
}

.presenter-view {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: var(--bg-primary);
  z-index: 1000;
  padding: 20px;
}

.presenter-view.active {
  display: flex;
  flex-direction: column;
}

.presenter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background: var(--bg-secondary);
  border-radius: 8px;
  margin-bottom: 20px;
}

.presenter-header .timer {
  font-size: 24px;
  font-weight: bold;
  font-family: var(--font-mono);
}

.presenter-header .slide-info {
  font-size: 18px;
  color: var(--text-secondary);
}

.presenter-header button {
  padding: 8px 16px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
}

.presenter-main {
  display: flex;
  flex: 1;
  gap: 20px;
}

.presenter-main .current-slide {
  flex: 2;
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.presenter-main .current-slide .slide-preview {
  width: 100%;
  height: 100%;
  transform-origin: center;
  transform: scale(0.5);
}

.presenter-main .side-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.presenter-main .next-slide {
  flex: 1;
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.presenter-main .next-slide .slide-preview {
  width: 100%;
  height: 100%;
  transform-origin: center;
  transform: scale(0.3);
  opacity: 0.7;
}

.presenter-main .notes {
  flex: 1;
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 20px;
  overflow: auto;
}

.presenter-main .notes h3 {
  font-size: 18px;
  margin-bottom: 10px;
  color: var(--text-secondary);
}

.presenter-main .notes p {
  font-size: 16px;
  line-height: 1.5;
}

.blackout {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: black;
  display: none;
  z-index: 500;
}

.blackout.active {
  display: block;
}

.overview-mode {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: var(--bg-primary);
  z-index: 900;
  padding: 40px;
  display: none;
  overflow: auto;
}

.overview-mode.active {
  display: block;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 30px;
  padding: 20px;
}

.overview-grid .slide-thumbnail {
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 20px;
  aspect-ratio: ${ratio.width} / ${ratio.height};
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  position: relative;
}

.overview-grid .slide-thumbnail:hover {
  transform: scale(1.02);
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}

.overview-grid .slide-thumbnail.active {
  border: 3px solid var(--accent);
}

.overview-grid .slide-thumbnail .slide-number {
  position: absolute;
  top: 10px;
  left: 10px;
  background: var(--accent);
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.time-display {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 10px 20px;
  background: var(--bg-secondary);
  border-radius: 8px;
  font-family: var(--font-mono);
  font-size: 18px;
  display: none;
  z-index: 400;
}

.time-display.active {
  display: block;
}

@media print {
  .slide {
    page-break-after: always;
    height: auto;
    position: relative;
    opacity: 1;
    visibility: visible;
    transform: none;
  }
  .controls, .presenter-view, .blackout, .overview-mode, .time-display {
    display: none !important;
  }
}

@media (max-width: 1024px) {
  .slide {
    padding: 40px;
  }
  .slide h1 {
    font-size: calc(var(--base-size) * var(--heading-scale) * 0.8);
  }
}

@media (max-width: 768px) {
  .slide {
    padding: 30px;
  }
  .slide h1 {
    font-size: calc(var(--base-size) * var(--heading-scale) * 0.6);
  }
  .slide p, .slide ul, .slide ol {
    font-size: calc(var(--base-size) * 0.8);
  }
}

@media (max-width: 480px) {
  .slide {
    padding: 20px;
  }
  .controls {
    bottom: 10px;
    gap: 10px;
  }
}
`;
}

export function generateJS(slideCount, options) {
  const transition = options.transition || 'slide';
  
  return `
(function() {
  'use strict';
  
  let currentSlide = 0;
  const totalSlides = ${slideCount};
  const transitionType = '${transition}';
  const slides = document.querySelectorAll('.slide');
  const prevBtn = document.querySelector('.controls .prev');
  const nextBtn = document.querySelector('.controls .next');
  const counter = document.querySelector('.slide-counter');
  const presenterView = document.querySelector('.presenter-view');
  const blackout = document.querySelector('.blackout');
  const overviewMode = document.querySelector('.overview-mode');
  const timeDisplay = document.querySelector('.time-display');
  let timerInterval = null;
  let startTime = null;
  let debounceTimeout = null;

  function updateSlide() {
    slides.forEach((slide, i) => {
      slide.classList.remove('active', 'prev');
      if (i === currentSlide) {
        slide.classList.add('active');
      } else if (i < currentSlide) {
        slide.classList.add('prev');
      }
    });

    if (prevBtn) prevBtn.disabled = currentSlide === 0;
    if (nextBtn) nextBtn.disabled = currentSlide === totalSlides - 1;
    if (counter) counter.textContent = (currentSlide + 1) + ' / ' + totalSlides;

    updatePresenterView();
    updateOverviewHighlights();
  }

  function nextSlide() {
    if (currentSlide < totalSlides - 1) {
      currentSlide++;
      updateSlide();
    }
  }

  function prevSlide() {
    if (currentSlide > 0) {
      currentSlide--;
      updateSlide();
    }
  }

  function goToSlide(index) {
    if (index >= 0 && index < totalSlides) {
      currentSlide = index;
      updateSlide();
    }
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  }

  function togglePresenterMode() {
    if (presenterView) {
      presenterView.classList.toggle('active');
      if (presenterView.classList.contains('active')) {
        startTimer();
      } else {
        stopTimer();
      }
    }
  }

  function toggleOverview() {
    if (overviewMode) {
      overviewMode.classList.toggle('active');
    }
  }

  function toggleBlackout() {
    if (blackout) {
      blackout.classList.toggle('active');
    }
  }

  function toggleTime() {
    if (timeDisplay) {
      timeDisplay.classList.toggle('active');
    }
  }

  function startTimer() {
    if (timerInterval) clearInterval(timerInterval);
    startTime = Date.now();
    timerInterval = setInterval(updateTimer, 1000);
    updateTimer();
  }

  function stopTimer() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  }

  function updateTimer() {
    const elapsed = Date.now() - startTime;
    const hours = Math.floor(elapsed / 3600000);
    const minutes = Math.floor((elapsed % 3600000) / 60000);
    const seconds = Math.floor((elapsed % 60000) / 1000);
    const timeStr = [hours, minutes, seconds].map(n => n.toString().padStart(2, '0')).join(':');
    const timerEl = document.querySelector('.presenter-header .timer');
    if (timerEl) timerEl.textContent = timeStr;
  }

  function updatePresenterView() {
    const currentSlideEl = document.querySelector('.presenter-main .current-slide .slide-content');
    const nextSlideEl = document.querySelector('.presenter-main .next-slide .slide-content');
    const notesEl = document.querySelector('.presenter-main .notes .notes-content');
    const slideInfoEl = document.querySelector('.presenter-header .slide-info');

    if (currentSlideEl && slides[currentSlide]) {
      currentSlideEl.innerHTML = slides[currentSlide].innerHTML;
    }
    if (nextSlideEl && slides[currentSlide + 1]) {
      nextSlideEl.innerHTML = slides[currentSlide + 1].innerHTML;
    }
    if (notesEl) {
      const notes = slides[currentSlide] ? slides[currentSlide].dataset.notes : '';
      notesEl.textContent = notes || 'No notes for this slide.';
    }
    if (slideInfoEl) {
      slideInfoEl.textContent = 'Slide ' + (currentSlide + 1) + ' of ' + totalSlides;
    }
  }

  function updateOverviewHighlights() {
    const thumbnails = document.querySelectorAll('.slide-thumbnail');
    thumbnails.forEach((thumb, i) => {
      thumb.classList.toggle('active', i === currentSlide);
    });
  }

  function handleKeydown(e) {
    if (debounceTimeout) return;
    
    debounceTimeout = setTimeout(() => {
      debounceTimeout = null;
    }, 100);

    const handled = {
      'ArrowRight': nextSlide,
      'ArrowLeft': prevSlide,
      'Space': (e) => { e.preventDefault(); nextSlide(); },
      'l': nextSlide,
      'h': prevSlide,
      'Home': () => goToSlide(0),
      'End': () => goToSlide(totalSlides - 1),
      'g': () => goToSlide(0),
      'G': () => goToSlide(totalSlides - 1),
      'f': toggleFullscreen,
      'p': togglePresenterMode,
      'o': toggleOverview,
      'Escape': () => {
        if (presenterView && presenterView.classList.contains('active')) {
          togglePresenterMode();
        }
        if (overviewMode && overviewMode.classList.contains('active')) {
          toggleOverview();
        }
        if (blackout && blackout.classList.contains('active')) {
          toggleBlackout();
        }
      },
      'b': toggleBlackout,
      't': toggleTime
    };

    if (handled[e.key]) {
      e.preventDefault();
      handled[e.key](e);
    }
  }

  function init() {
    document.addEventListener('keydown', handleKeydown);
    
    if (prevBtn) prevBtn.addEventListener('click', prevSlide);
    if (nextBtn) nextBtn.addEventListener('click', nextSlide);

    const exitPresenter = document.querySelector('.presenter-header button');
    if (exitPresenter) exitPresenter.addEventListener('click', togglePresenterMode);

    updateSlide();

    const thumbnails = document.querySelectorAll('.slide-thumbnail');
    thumbnails.forEach((thumb, i) => {
      thumb.addEventListener('click', () => {
        goToSlide(i);
        toggleOverview();
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
`;
}

export function render(presentation, options = {}) {
  const themeName = options.theme || 'default';
  const theme = getTheme(themeName);
  const title = options.title || presentation.metadata.title || 'Presentation';
  const author = options.author || presentation.metadata.author || '';
  const transition = options.transition || 'slide';
  const aspectRatio = options.aspectRatio || '16:9';

  const css = generateCSS(theme, aspectRatio);
  const js = generateJS(presentation.slides.length, { transition });

  const slidesHtml = presentation.slides.map((slide, index) => {
    const notesAttr = slide.notes ? ` data-notes="${escapeHtmlAttr(slide.notes)}"` : '';
    return `<section class="slide" data-slide="${index}"${notesAttr}>${slide.html}</section>`;
  }).join('\n');

  const overviewSlides = presentation.slides.map((slide, index) => {
    return `<div class="slide-thumbnail" data-slide="${index}">
      <span class="slide-number">${index + 1}</span>
      <div class="slide-preview">${slide.html}</div>
    </div>`;
  }).join('\n');

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="format-detection" content="telephone=no">
  <meta name="theme-color" content="${theme.vars['--bg-primary']}">
  <title>${escapeHtml(title)}</title>
  <style>
${css}
  </style>
</head>
<body>
  <div class="presentation">
    <div class="slides">
${slidesHtml}
    </div>

    <nav class="controls">
      <button class="prev" disabled>←</button>
      <span class="slide-counter">1 / ${presentation.slides.length}</span>
      <button class="next">→</button>
    </nav>
  </div>

  <div class="presenter-view">
    <div class="presenter-header">
      <span class="timer">00:00:00</span>
      <span class="slide-info">Slide 1 of ${presentation.slides.length}</span>
      <button class="exit">Exit Presenter View</button>
    </div>
    <div class="presenter-main">
      <div class="current-slide">
        <div class="slide-content"></div>
      </div>
      <div class="side-panel">
        <div class="next-slide">
          <div class="slide-content"></div>
        </div>
        <div class="notes">
          <h3>Speaker Notes</h3>
          <p class="notes-content">No notes for this slide.</p>
        </div>
      </div>
    </div>
  </div>

  <div class="blackout"></div>

  <div class="overview-mode">
    <div class="overview-grid">
${overviewSlides}
    </div>
  </div>

  <div class="time-display"></div>

  <script>
${js}
  </script>
</body>
</html>`;
}

export function renderSlide(slide, theme) {
  return `<section class="slide">${slide.html}</section>`;
}

export { getAllThemes };