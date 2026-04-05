import { Component, createSignal, createEffect } from 'solid-js';

interface ThumbnailProps {
  initialSrc: string;
  videoId?: string;
  title: string;
}

export const Thumbnail: Component<ThumbnailProps> = (props) => {
  const [currentSrc, setCurrentSrc] = createSignal(props.initialSrc);
  const [hasError, setHasError] = createSignal(false);

  createEffect(() => {
    setCurrentSrc(props.initialSrc);
    setHasError(false);
  });

  const handleError = () => {
    if (!hasError()) {
      if (props.videoId) {
        setCurrentSrc(`https://img.youtube.com/vi/${props.videoId}/default.jpg`);
        setHasError(true);
      } else {
        setCurrentSrc('https://placehold.co/160x90?text=Thumbnail');
        setHasError(true);
      }
    }
  };

  return (
    <img
      src={currentSrc()}
      alt={props.title}
      class="w-full h-full object-cover"
      onError={handleError}
      loading="lazy"
    />
  );
};
