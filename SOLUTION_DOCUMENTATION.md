# Hawkeye Audio Processing Solution

## Overview
This Power Automate solution package provides automated audio processing capabilities including transcription, AI-powered summarization, and intelligent insights generation.

## Solution Details

**Solution Name:** HawkeyeAudioProcessing
**Version:** 1.0.0.0
**Publisher:** Hawkeye Publisher
**Package File:** HawkeyeAudioProcessing.zip
**Package Size:** 16KB
**MD5 Checksum:** edcd7ddea86a733a684f58faa3c7ea3e

## Components Included

### Flows

#### 1. Parent Audio Processing Flow
- **Name:** hawkeye_ParentAudioFlow
- **Type:** Automated Cloud Flow
- **Trigger:** When a file is created in OneDrive folder
- **Purpose:** Orchestrates the entire audio processing workflow
- **Actions:**
  - Monitors OneDrive folder for new audio files
  - Renames files using convention: `MTG001_YYYY_MM_DD_DESCRIPTION.ext`
  - Calls child flows for processing
  - Manages file lifecycle

#### 2. Child Flow - OneNote and Transcript
- **Name:** hawkeye_ChildFlowOneNote
- **Type:** Manual/Child Flow
- **Purpose:** Creates OneNote pages and exports transcripts
- **Actions:**
  - Transcribes audio using Azure Cognitive Services Speech
  - Creates OneNote page with audio and transcript
  - Exports transcript to `.txt` file in `/Hawkeye/Transcripts/`
  - Returns transcript content to parent flow

#### 3. Child Flow - AI Summary and PDF
- **Name:** hawkeye_ChildFlowAISummary
- **Type:** Manual/Child Flow
- **Purpose:** Generates AI-powered insights and PDF reports
- **Actions:**
  - Summarizes transcript using AI Builder GPT
  - Generates insights and pattern analysis
  - Creates formatted HTML report
  - Converts report to PDF
  - Saves PDF in `/Hawkeye/Summaries/`

### Environment Variables

1. **hawkeye_AudioFolderPath**
   - Default: `/Hawkeye/Audio Recordings/`
   - Purpose: OneDrive folder path for audio recordings

2. **hawkeye_TranscriptFolderPath**
   - Default: `/Hawkeye/Transcripts/`
   - Purpose: OneDrive folder path for transcript files

3. **hawkeye_SummaryFolderPath**
   - Default: `/Hawkeye/Summaries/`
   - Purpose: OneDrive folder path for summary PDF files

4. **hawkeye_MeetingIdentifierPrefix**
   - Default: `MTG001`
   - Purpose: Prefix for meeting file naming convention

## Required Connectors

The solution uses the following Power Platform connectors:

1. **OneDrive for Business** - File storage and management
2. **Azure Cognitive Services Speech** - Audio transcription
3. **OneNote (Business)** - Note-taking and organization
4. **AI Builder GPT** - AI-powered text analysis and summarization
5. **Content Conversion** - HTML to PDF conversion

## File Naming Convention

All processed files follow this naming convention:
```
{Prefix}_{YYYY}_{MM}_{DD}_{Description}.{extension}
```

Example:
```
MTG001_2025_11_19_QuarterlyReview.mp3
MTG001_2025_11_19_QuarterlyReview.txt
MTG001_2025_11_19_QuarterlyReview.pdf
```

## Folder Structure Required

Before importing, ensure these OneDrive folders exist:

```
/Hawkeye/
├── Audio Recordings/    (Source folder for audio files)
├── Transcripts/         (Output folder for text transcripts)
└── Summaries/          (Output folder for PDF summaries)
```

## Import Instructions

### Step 1: Access Power Automate
1. Navigate to https://make.powerautomate.com
2. Sign in with your Microsoft 365 account
3. Ensure you're in the correct environment

### Step 2: Import Solution
1. Click **Solutions** in the left navigation
2. Click **Import solution** at the top
3. Click **Browse** and select `HawkeyeAudioProcessing.zip`
4. Click **Next**

### Step 3: Configure Connections
During import, you'll need to configure connections:

1. **OneDrive for Business**
   - Click **Select a connection** or **Create new**
   - Authenticate with your OneDrive credentials

2. **Azure Cognitive Services Speech**
   - Click **Select a connection** or **Create new**
   - Provide your Cognitive Services API key and endpoint

3. **OneNote (Business)**
   - Click **Select a connection** or **Create new**
   - Authenticate with your Microsoft 365 account

4. **AI Builder GPT**
   - Click **Select a connection** or **Create new**
   - Ensure AI Builder is enabled in your environment

5. **Content Conversion**
   - Click **Select a connection** or **Create new**
   - Authenticate as needed

### Step 4: Configure Environment Variables
Review and update environment variables if needed:

1. **hawkeye_AudioFolderPath** - Confirm or update folder path
2. **hawkeye_TranscriptFolderPath** - Confirm or update folder path
3. **hawkeye_SummaryFolderPath** - Confirm or update folder path
4. **hawkeye_MeetingIdentifierPrefix** - Update if using different prefix

### Step 5: Complete Import
1. Click **Import** to begin the import process
2. Wait for the import to complete (usually 1-2 minutes)
3. Review the import summary for any warnings or errors

### Step 6: Activate Flows
After import:

1. Open the **HawkeyeAudioProcessing** solution
2. Locate each flow:
   - Parent Audio Processing Flow
   - Child Flow - OneNote and Transcript
   - Child Flow - AI Summary and PDF
3. Turn on each flow using the toggle switch

## Testing the Solution

### Test Procedure
1. Ensure all three OneDrive folders exist
2. Verify all flows are turned on
3. Upload a test audio file to `/Hawkeye/Audio Recordings/`
4. Monitor flow run history in Power Automate
5. Check outputs in:
   - `/Hawkeye/Audio Recordings/` - Renamed audio file
   - `/Hawkeye/Transcripts/` - Text transcript
   - `/Hawkeye/Summaries/` - PDF summary
   - OneNote - New page with audio and transcript

### Expected Results
- Audio file renamed to `MTG001_YYYY_MM_DD_{original_name}.{ext}`
- Transcript file created as `.txt`
- Summary PDF created with AI-generated insights
- OneNote page created with full content

## Troubleshooting

### Common Issues

**Issue:** Import fails with schema validation errors
- **Solution:** Ensure you're using a compatible Power Platform environment (latest version recommended)

**Issue:** Flows don't trigger automatically
- **Solution:**
  - Verify flows are turned on
  - Check connection authentication
  - Ensure OneDrive folder path is correct

**Issue:** Transcription fails
- **Solution:**
  - Verify Azure Cognitive Services connection
  - Check API quota and limits
  - Ensure audio file format is supported (MP3, WAV, M4A)

**Issue:** AI Builder GPT not available
- **Solution:**
  - Verify AI Builder is enabled in your environment
  - Check licensing requirements
  - Ensure you have AI Builder credits

**Issue:** PDF generation fails
- **Solution:**
  - Check Content Conversion service availability
  - Verify HTML formatting in compose action
  - Ensure sufficient Power Platform storage

### Required Licenses

- Microsoft 365 (for OneDrive, OneNote)
- Power Automate Premium or Per-User license
- AI Builder credits (for GPT and Speech services)
- Azure Cognitive Services subscription (for Speech-to-Text)

## Solution Architecture

```
┌─────────────────────────────────────────────────┐
│  OneDrive: /Hawkeye/Audio Recordings/          │
│  (Trigger: New file added)                      │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│  Parent Flow: Audio Processing                  │
│  - Rename file (MTG001_YYYY_MM_DD_DESC.ext)    │
│  - Coordinate child flows                       │
└───────┬─────────────────────────┬───────────────┘
        │                         │
        ▼                         ▼
┌──────────────────┐    ┌───────────────────────┐
│ Child Flow 1:    │    │ Child Flow 2:         │
│ OneNote          │    │ AI Summary            │
│ - Transcribe     │───▶│ - Summarize           │
│ - Create page    │    │ - Generate insights   │
│ - Export .txt    │    │ - Create PDF          │
└──────────────────┘    └───────────────────────┘
        │                         │
        ▼                         ▼
┌──────────────────┐    ┌───────────────────────┐
│ /Transcripts/    │    │ /Summaries/           │
│ MTG001_*.txt     │    │ MTG001_*.pdf          │
└──────────────────┘    └───────────────────────┘
```

## Customization Options

### Modify File Naming Convention
Edit the `Compose_New_File_Name` action in Parent Flow:
- Change date format
- Modify prefix logic
- Add additional metadata

### Add Custom Prompts
Edit AI Builder GPT prompts in Child Flow 2:
- Customize summary format
- Add specific analysis requirements
- Modify insight categories

### Extend Processing
Add new child flows for:
- Email notifications
- Calendar event creation
- SharePoint document library integration
- Teams channel posting

## Support and Maintenance

### Version History
- **1.0.0.0** (2025-11-19) - Initial release

### Known Limitations
- Maximum audio file size: Limited by OneDrive and Cognitive Services quotas
- Transcription languages: Currently set to English (en-US)
- AI Builder token limits apply to GPT operations
- Concurrent flow runs may be throttled based on license

### Future Enhancements
- Multi-language transcription support
- Speaker diarization
- Integration with Microsoft Teams
- Real-time transcription option
- Custom AI model training

## License and Compliance

This solution requires appropriate Microsoft 365 and Power Platform licenses. Ensure compliance with:
- Data residency requirements
- Privacy and security policies
- Audio recording consent laws
- AI usage policies

## Contact and Feedback

For issues, questions, or feature requests related to this solution package, please contact your Power Platform administrator or submit feedback through the Power Automate portal.

---

**Generated:** 2025-11-19
**Solution Package:** HawkeyeAudioProcessing.zip
**Documentation Version:** 1.0
