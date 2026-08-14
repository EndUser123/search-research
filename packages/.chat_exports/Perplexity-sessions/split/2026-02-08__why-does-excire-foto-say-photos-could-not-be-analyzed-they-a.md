---
title: "why does excire foto say photos could not be analyzed?  they are actually videos"
date: "2026-02-08"
mode: "CONCISE"
uuid: "a057eb72-a3bc-49fd-81a3-19da079f70fc"
entry_count: 6
---

## Human

why does excire foto say photos could not be analyzed?  they are actually videos

## Assistant

Excire Foto primarily analyzes photos but supports limited video analysis by extracting a preview frame for AI tagging and searching. The "photos could not be analyzed" error occurs when it encounters videos because its core analysis engine is optimized for still images, and certain video formats or codecs fail preview generation or processing.[1]

## Common Causes
- **Unsupported formats/codecs**: AVI, MKV, WEBM, WMV often fail on macOS; H.265 HDR (10-bit), ProRes unsupported on Windows.[1]
- **Platform differences**: Windows supports more formats like AVI but needs extensions (e.g., HEVC); macOS handles MOV/MP4 better but skips others.[1]
- **Mixed catalogs**: Scanning folders with videos alongside photos triggers errors or slowdowns during initial indexing.[2]

## Fixes
- Filter videos out using the filter bar (RAW/non-RAW/video toggle) before analysis.[3]
- Use Excire Foto 2025+ for improved video preview support on compatible formats like MP4/H.264.[4][1]
- Ensure system codecs are installed (e.g., Microsoft HEVC extension on Windows); restart and re-add folders.[1]

## Human

how can we enable the analysis?

## Assistant

Excire Foto analyzes videos by automatically extracting and tagging a representative preview frame during catalog import or registration—no manual toggle is needed to "enable" it, as long as your version supports videos (2025 or later) and the format is compatible.[1][2]

## Enable Video Analysis
- Update to Excire Foto 2025+ for full video support, including AI keywording on extracted frames.[2][3]
- Add videos to your catalog: Go to "Add Folders," select video-containing directories, and let indexing run—analysis happens automatically post-registration if "Analyze after registration" is enabled in settings.[4][5]
- Install platform codecs: On Windows, add Microsoft HEVC Video Extension for H.265; on macOS, ensure QuickTime supports the format.[1]

## Troubleshooting
- **Compatible formats**: MP4, MOV (both OS), AVI/MKV (Windows only)—unsupported ones skip analysis.[1]
- Filter videos first (via filter bar) if mixed folders cause errors, then re-scan.[6]
- Restart app, clear cache if needed, or check support.excire.com for codec guides.[1]

## Human

I'm already on excire foto 2025 v4.1.0+

what's the best solution for enabling for H.265 for windows 11 for excire foto 2025?

## Assistant

The best solution for enabling H.265 (HEVC 8-bit) analysis in Excire Foto 2025 v4.1.0+ on Windows 11 is installing the official Microsoft HEVC Video Extensions from the Microsoft Store, as Excire relies on Windows system codecs for video preview generation and AI analysis.[1]

## Installation Steps
- Open Microsoft Store, search "HEVC Video Extensions from Device Manufacturer" or "HEVC Video Extensions."
- Install the free OEM version if available (prevents prompts on compatible hardware); otherwise, buy the $0.99 version.[2][3]
- Restart Excire Foto, remove/re-add the video folders, and trigger re-analysis—H.265 videos should now generate previews for tagging.

## Key Notes
- Note: 10-bit HDR H.265 remains unsupported in Excire on Windows.
- Verify in File Explorer first: H.265 videos should show thumbnails post-install.
- Alternative: Transcode incompatible videos to H.264/MP4 using tools like HandBrake before import.[2]

## Human

Are there free alternatives to HEVC Video Extensions that work with Excire Foto

## Assistant

Free alternatives to Microsoft's HEVC Video Extensions exist for Windows 11, but Excire Foto specifically requires system-level DirectShow/FFmpeg-compatible codecs for reliable video preview extraction and analysis—third-party packs like K-Lite or LAV Filters are the most reliable free options that work system-wide, including for apps like Excire.[1][2]

## Recommended Free Codecs
| Codec Pack | Key Features | Download Source | Excire Compatibility Notes |
|------------|--------------|-----------------|------------------------|
| K-Lite Codec Pack (Full/Basic) | Comprehensive DirectShow filters for H.265, customizable, supports Excire previews. | codecguide.com | Highly recommended for photo apps; users confirm H.265 video thumbnails/analysis in similar tools.[2] |
| LAV Filters | Lightweight, open-source HEVC decoder for VLC/DirectShow apps. | github.com/Nevcairiel/LAVFilters | Integrates well; enables system playback/previews for Excire.[1] |
| Media Player Codec Pack | Broad format support, free for Windows Media Player integration. | mpc-hc.org | Good for basic H.265; less customizable than K-Lite.[2] |

## Installation Tips
- Download K-Lite Basic/Standard from official site, install with HEVC enabled (default), restart PC and Excire Foto.[2]
- Test: Check if H.265 videos show thumbnails in Windows Explorer first; re-scan folders in Excire.
- Avoid shady "free OEM" APNX bundles—risk malware; stick to trusted packs.[3][4]
- Fallback: Transcode videos to H.264 via HandBrake (free).[5]

## Human

they do show with thumbnails in windows explorer, but not in excire foto.

## Assistant

Thumbnails showing in Windows Explorer but not Excire Foto indicates an app-specific preview cache or codec filter issue, as Excire generates its own thumbnails from system video decoding during import but may cache failures for unsupported/partial codec support.[1]

## Quick Fixes
- **Re-register videos**: Right-click affected videos/folders in Excire > "Remove from database" (don't delete files), then "Synchronize" or "Add folders" to force re-analysis and preview generation.[2]
- **Clear Excire cache**: Close app, delete contents of `%AppData%\excire\Foto\cache` or `thumbs` folder (backup first), restart, and re-sync.[3]
- **Codec tweak**: If using K-Lite/LAV, open its "Codec Tweak Tool" > Thumbnails tab > Enable all video formats (H.265 included) > Apply.[4]

## Advanced Steps
- Verify "Analyze after registration" is on in Settings > Registration.[5]
- Restart Excire in admin mode; ensure no antivirus blocks video decoding.
- If persistent, contact Excire support with video sample—may be 10-bit H.265 limit or v4.1.0+ bug.[1]

## Human

Is there something like excire foto, except for videos?

## Assistant

No direct video-only equivalent to Excire Foto exists, as most AI media managers focus on photos with varying video support, but several tools excel at video organization, tagging, and AI search for large libraries.

## Top Video-Focused Alternatives
| Tool | Key Features | Platforms | Pricing |
|------|--------------|-----------|---------|
| **Mylio Photos** | AI tagging/faces on video keyframes, duplicate detection, cross-device sync; strong video handling alongside photos.[1] | Windows, Mac, Mobile | Freemium ($99+/yr premium) |
| **Tonfotos** | Video face recognition, keyword AI, timeline organization; optimized for mixed photo/video libraries of 100k+ files.[10] | Windows, Mac | $49 one-time |
| **ACDSee Photo Studio Ultimate 2025** | Video previews, AI keywords, metadata search; better video support than Excire without import silos.[3] | Windows, Mac | $149 one-time |
| **digiKam** (free) | Face recognition on videos, tag search, advanced filtering; open-source with solid video thumbnail/AI tools.[5] | Windows, Mac, Linux | Free |
| **Peakto** | Meta-catalog AI search across video/photo catalogs; extracts video keywords but Mac-only.[1] | Mac | $19/mo |

## Recommendations
For Windows 11 like your setup, start with Mylio or Tonfotos—they handle H.265 videos reliably post-codec install and offer Excire-like AI without photo bias. Test free trials to confirm thumbnail/analysis matches your workflow.[1][10]
