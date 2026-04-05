# Vid_ReC Configuration Guide

This document explains all the available settings in the `config.toml` file for the Vid_ReC application.

## `[paths]`

This section defines the core input and output locations for the application.

| Key      | Type   | Default Value               | Description                                                        |
| :------- | :----- | :-------------------------- | :----------------------------------------------------------------- |
| `source` | String | (Required)                  | The full path to the root directory containing your video library. |
| `temp_dir` | String | `"C:/Temp/ReencodedVideos"` | The full path to a temporary directory for storing intermediate files. This directory will be cleared on each run. |

---

## `[settings]`

This section contains general on/off toggles for major application features.

| Key                | Type    | Default Value | Description                                                              |
| :----------------- | :------ | :------------ | :----------------------------------------------------------------------- |
| `no_replace`       | Boolean | `false`       | If `true`, the script will not replace original files. The final processed videos will be left in the `temp_dir`. |
| `create_subtitles` | Boolean | `true`        | If `true`, the application will generate English subtitles for any videos that do not already have them. |
| `normalize_audio`  | Boolean | `false`       | If `true`, the audio for all processed videos will be normalized to the ITU-R BS.1770-4 loudness standard. |

---

## `[encoding]`

This section controls the parameters sent to `ffmpeg` for video re-encoding.

| Key             | Type    | Default Value | Description                                                              |
| :-------------- | :------ | :------------ | :----------------------------------------------------------------------- |
| `target_height` | Integer | `1080`        | The target vertical resolution for the output video. If a source video is taller than this, it will be downscaled. Set to `0` to disable all downscaling. |
| `crf`           | Integer | `0`           | The Constant Rate Factor (CRF) for x265 encoding. A lower value means higher quality and larger file size. Recommended range is 22-28. A value of `0` enables auto-calculation based on source bitrate. |


## `[quality]`

This section controls the intelligent decision-making logic based on video quality metrics.

| Key                         | Type    | Default Value | Description                                                              |
| :-------------------------- | :------ | :------------ | :----------------------------------------------------------------------- |
| `vmaf_decision_enabled`     | Boolean | `true`        | If `true`, a re-encoded file will only be kept if it meets the VMAF score threshold AND is smaller than the original. |
| `vmaf_decision_threshold`   | Float   | `94.0`        | The VMAF score (0-100) the new file must exceed to be considered for replacement. |

---

## `[performance]`

This section allows for tuning the resource usage of the application.

| Key           | Type    | Default Value | Description                                                              |
| :------------ | :------ | :------------ | :----------------------------------------------------------------------- |
| `max_workers` | Integer | `0`           | The maximum number of files to process in parallel during the CPU-intensive encoding phase. A value of `0` enables auto-detection, using all available CPU cores. |

**Related ADRs:**
- [ADR-008: SQLAlchemy SQLite for Domain Models](../architecture/adr/ADR-008_SQLAlchemy_SQLite_for_Domain_Models.md)
