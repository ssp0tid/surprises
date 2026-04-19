export function openPresenterWindow(slideData) {
  const presenterUrl = 'presenter.html';
  const presenterWindow = window.open(presenterUrl, 'PresenterView', 'width=1200,height=800');
  return presenterWindow;
}

export function syncPresenter(currentSlideIndex) {
  try {
    const channel = new BroadcastChannel('slidemd-presenter');
    channel.postMessage({ type: 'slide', index: currentSlideIndex });
  } catch (e) {
    localStorage.setItem('slidemd-slide', JSON.stringify({
      type: 'slide',
      index: currentSlideIndex,
      timestamp: Date.now()
    }));
  }
}

export function closePresenterWindow() {
  try {
    const channel = new BroadcastChannel('slidemd-presenter');
    channel.postMessage({ type: 'close' });
  } catch (e) {
    localStorage.setItem('slidemd-slide', JSON.stringify({
      type: 'close',
      timestamp: Date.now()
    }));
  }
}

export function setupPresenterListener(callback) {
  try {
    const channel = new BroadcastChannel('slidemd-presenter');
    channel.onmessage = (event) => {
      if (event.data.type === 'slide') {
        callback(event.data.index);
      } else if (event.data.type === 'close') {
        callback('close');
      }
    };
    return () => channel.close();
  } catch (e) {
    const handler = (e) => {
      if (e.key === 'slidemd-slide') {
        const data = JSON.parse(e.newValue);
        if (data.type === 'slide') {
          callback(data.index);
        } else if (data.type === 'close') {
          callback('close');
        }
      }
    };
    window.addEventListener('storage', handler);
    return () => window.removeEventListener('storage', handler);
  }
}