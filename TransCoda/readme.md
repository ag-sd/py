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
- [x] Show CPU, Thread and Memory statistics
- [ ] Redirect STDERR to a file
- [x] Add encoded ratio (Input fs vs Output fs)
- [ ] Run process after execution
- [ ] Option to wipe out tags after encode
- [x] Handle output file exists
- [x] Remove selected files from encode list
- [x] Save input file dates on output file
- [ ] Preserve encode list across application restart
- [x] ~~Mutagen~~ `ffprobe` integration for advanced media information
- [ ] Configure output directory by tags
- [ ] Select multiple files
- [x] Extended columns available
- [ ] Column Sort
- [ ] Configure Encoders from File
<del>
- [ ] Extended format support<br>
  - [x] .aac<br>
  - [x] .aiff<br>
  - [x] .amr<br>
  - [x] .opus<br>
  - [x] .ts</del>

### Changelog
**Friday Apr 24 2020 (EDT)** 
- Handle output file exists
- Save input file dates on output file
- `ffprobe` integration for advanced media information
- Extended columns available

**Saturday, April 18, 2020 (EDT)**
- Duplicate Image Finder Multi-Threaded performance optimisations
- Improved image display grid for duplicate images
- Improved metadata preview for duplicate images