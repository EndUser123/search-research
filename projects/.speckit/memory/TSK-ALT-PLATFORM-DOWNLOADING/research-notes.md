# Research Notes - Alt-Platform Support

## Key Findings from Research
- yt-dlp supports 1000+ sites including Odysee, Rumble, BitChute
- Odysee/LBRY provides blockchain-based permanent content
- aria2c integration provides superior fragment handling
- Proxy rotation essential for rate limit management

## Platform-Specific Considerations

### Odysee/LBRY
- Blockchain-based content storage
- Claim IDs for permanent references
- Original quality files available
- Limited transcript support

### Rumble
- Growing platform with good yt-dlp support
- Rate limiting considerations
- Variable transcript availability

### BitChute
- Alternative platform support
- Different API patterns
- Content moderation considerations

## Technical Requirements
- Platform detection from URLs
- Unified error handling
- Metadata preservation
- Quality profile management

## Commands for Testing
```bash
# Test Odysee support
yt-dlp --simulate "https://odysee.com/@TwoMinutePapers:"

# Test Rumble support
yt-dlp --simulate "https://rumble.com/c/somechannel"

# Test aria2c integration
yt-dlp --external-downloader aria2c --external-downloader-args "aria2c:-x 16 -s 16 -j 16"
```