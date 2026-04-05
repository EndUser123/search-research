import { Component, createSignal, onMount, Show } from 'solid-js';
import { SourceUrlsPanel } from './components/SourceUrlsPanel';

const App: Component = () => {
  const [urls, setUrls] = createSignal('');
  const [originalUrls, setOriginalUrls] = createSignal('');
  const [sourceUrlFilter, setSourceUrlFilter] = createSignal<'all' | 'videos' | 'playlists'>('all');
  const [error, setError] = createSignal('');
  const [isDragging, setIsDragging] = createSignal(false);
  const [stage1PanelsCollapsed, setStage1PanelsCollapsed] = createSignal({ sourceUrls: false, discoveredItems: false, stagingQueue: false });
  const [panelFlex] = createSignal({ sourceUrls: 1, discoveredItems: 1, stagingQueue: 1 });

  let fileInputRef: HTMLInputElement | undefined;

  const toggleStage1Panel = (panel: 'sourceUrls' | 'discoveredItems' | 'stagingQueue') => {
    setStage1PanelsCollapsed(p => ({ ...p, [panel]: !p[panel] }));
  };

  const handleUrlsTextAreaChange = (e: any) => {
    setUrls(e.target.value);
  };

  const handleCleanUrls = () => {
    const lines = originalUrls().split('\n');
    const validLines = lines.filter((line: string) => line.trim() !== '' && line.startsWith('http'));
    const cleanedContent = validLines.join('\n');

    if (validLines.length > 0) {
      setOriginalUrls(cleanedContent);
      setUrls(cleanedContent);
    }
  };

  const handleSaveUrls = () => {
    // Simple save functionality
    localStorage.setItem('vip_urls', originalUrls());
  };

  const handleClearUrls = () => {
    setOriginalUrls('');
    setUrls('');
  };

  const handleUrlSubmit = () => {
    // Simple submit functionality for testing
    console.log('Submitting URLs:', urls().split('\n').filter((u: string) => u.trim()));
  };

  const handleFileInputChange = (e: any) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const content = event.target?.result as string;
        if (content) {
          setOriginalUrls(content);
          setUrls(content);
        }
      };
      reader.readAsText(file);
    }
  };

  const handleDragOver = (e: any) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: any) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: any) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file && file.type === 'text/plain') {
        const reader = new FileReader();
        reader.onload = (event) => {
          const content = event.target?.result as string;
          if (content) {
            setOriginalUrls(content);
            setUrls(content);
          }
        };
        reader.readAsText(file);
      }
    }
  };

  const handleImportClick = () => {
    fileInputRef?.click();
  };

  onMount(() => {
    // Load any saved URLs
    const saved = localStorage.getItem('vip_urls');
    if (saved) {
      setOriginalUrls(saved);
      setUrls(saved);
    }
  });

  return (
    <div class="flex flex-col h-screen bg-background-primary text-text-primary">
      <header class="p-4 border-b border-border-secondary bg-background-secondary">
        <h1 class="text-2xl font-bold">VIP - YouTube Analysis Tool</h1>
      </header>

      <main class="flex-grow overflow-auto p-4">
        <div class="max-w-6xl mx-auto">
          <SourceUrlsPanel
            urls={urls()}
            originalUrls={originalUrls()}
            sourceUrlFilter={sourceUrlFilter()}
            handleSourceUrlFilterChange={setSourceUrlFilter}
            handleCleanUrls={handleCleanUrls}
            handleClearUrls={handleClearUrls}
            handleSaveUrls={handleSaveUrls}
            handleUrlSubmit={handleUrlSubmit}
            handleUrlTextAreaChange={handleUrlsTextAreaChange}
            handleImportClick={handleImportClick}
            fileInputRef={fileInputRef}
            handleFileInputChange={handleFileInputChange}
            error={error()}
            isDragging={isDragging()}
            handleDragOver={handleDragOver}
            handleDragLeave={handleDragLeave}
            handleDrop={handleDrop}
            stage1PanelsCollapsed={stage1PanelsCollapsed()}
            toggleStage1Panel={toggleStage1Panel}
            panelFlex={panelFlex()}
          />
        </div>
      </main>

      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileInputChange}
        class="hidden"
        accept=".txt,text/plain"
      />
    </div>
  );
};

export default App;
