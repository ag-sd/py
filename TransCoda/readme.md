# Trans:Coda - A ffmpeg based transcoder for media files
Trans:Coda lets you convert media from one format to another

### Features
* Drag and drop audio files into application
* Several encoder configurations available
* Multi-threaded encoding makes the process blazing fast

### TO-DO
- [x] Drag and drop folder to add all files from it
- [x] Realtime file encode status
- [x] Change status of files in encode list - (Change back to Ready or mark as complete)
- [x] Show CPU, Thread ~~and Memory statistics~~
- [ ] Redirect STDERR to a file
- [x] Add encoded ratio (Input fs vs Output fs)
- [ ] Run a process after execution
- [x] Option to wipe out tags after encode
- [x] Handle output file exists
- [x] Remove selected files from encode list
- [x] Save input file dates on output file
- [x] Preserve encode list across application restart
- [x] ~~Mutagen~~ `ffprobe` integration for advanced media information
- [ ] Configure output directory by tags ex base_dir/%genre - %album/...
- [x] Select multiple files
- [x] Extended columns available
- [x] Column Sort
- [x] Advanced Encoder configuration
- [x] Configure Encoders from File
- [x] Support any encoder
- [x] Add Encoder history to skip files that have previously been encoded
- [x] Start Encoding largest/oldest/longest files first
- [x] Add Support for keyboard shortcuts
- [ ] Realtime sorting of data as results change
- [ ] If media kbps < min of encoder, just copy the file over
- [x] Copy everything else from the source folder that's not a media file
  - [x] Add ability to configure this
- [ ] Profiles
- [ ] Configure option to load metadata  
- [ ] Split and Encode Cue files: 
  - https://unix.stackexchange.com/questions/10251/how-do-i-split-a-flac-with-a-cue
  - https://stackoverflow.com/questions/46508055/using-ffmpeg-to-cut-audio-from-to-position
- [ ] Download links specified in a playlist.m3u file 
- [ ] Youtube audio downloader
  - https://stackoverflow.com/questions/40713268/download-youtube-video-using-python-to-a-certain-directory
  - https://github.com/ytdl-org/youtube-dl/blob/master/README.md#readme
- [ ] ~~Change the encoder on a file~~

- [ ] Extended format support<br>
  - [x] .aac<br>
  - [x] .aiff<br>
  - [x] .amr<br>
  - [x] .opus<br>
  - [x] .ts</del>
  
### Known Bugs
- [ ] Initial size is not formatted correctly

### Changelog
**Tuesday May 12 2020 (EDT)** 
- Select multiple files in files window
- Option to wipe out tags after encode
- Ability to choose number of simultaneous threads for background activity
- Better visual cues about background activity
- GUI improvements
- Progressbar in each file row
- Bugfixes

**Friday Apr 24 2020 (EDT)** 
- Handle output file exists
- Save input file dates on output file
- `ffprobe` integration for advanced media information
- Extended columns available

**Saturday, April 18, 2020 (EDT)**
- Duplicate Image Finder Multi-Threaded performance optimisations
- Improved image display grid for duplicate images
- Improved metadata preview for duplicate images